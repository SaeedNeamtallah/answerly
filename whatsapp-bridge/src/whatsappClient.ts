import {
  makeWASocket,
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion,
  WASocket,
  makeCacheableSignalKeyStore,
  Browsers,
} from '@whiskeysockets/baileys';
import { Boom } from '@hapi/boom';
import pino from 'pino';
import fs from 'fs';
import path from 'path';

const logger = pino({ level: 'info' });
const sessionsDir = process.env.WHATSAPP_SESSION_DIR || path.join(process.cwd(), 'sessions');
const backendUrl = (process.env.BACKEND_URL || 'http://backend:8000').replace(/\/+$/, '');
const reconnectDelayMs = parsePositiveInt(process.env.WHATSAPP_RECONNECT_DELAY_MS, 5000);
const maxReconnectAttempts = parsePositiveInt(process.env.WHATSAPP_RECONNECT_MAX_ATTEMPTS, 5);
const maxQrAttempts = parsePositiveInt(process.env.WHATSAPP_QR_MAX_ATTEMPTS, 3);
const qrTtlMs = parsePositiveInt(process.env.WHATSAPP_QR_TTL_MS, 10 * 60 * 1000);

if (!fs.existsSync(sessionsDir)) {
  fs.mkdirSync(sessionsDir, { recursive: true });
}

type SessionStatus = 'initializing' | 'qr_ready' | 'connected' | 'disconnected' | 'expired' | 'error';

interface SessionData {
  sock: WASocket;
  qr: string | null;
  status: SessionStatus;
  reconnectAttempts: number;
  qrAttempts: number;
  startedAt: number;
  lastActivityAt: number;
  lastError: string | null;
  reconnectTimer?: NodeJS.Timeout;
  qrExpiryTimer?: NodeJS.Timeout;
}

const sessions = new Map<string, SessionData>();

function parsePositiveInt(value: string | undefined, fallback: number) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? Math.floor(parsed) : fallback;
}

function sessionPathFor(sessionId: string) {
  return path.join(sessionsDir, sessionId);
}

async function reportSessionStatus(sessionId: string, status: SessionStatus, lastError?: string | null) {
  try {
    await fetch(`${backendUrl}/whatsapp/webhook/${sessionId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, last_error: lastError || null }),
    });
  } catch (err) {
    logger.warn({ err, sessionId, status }, 'Failed to report WhatsApp session status to backend');
  }
}

function setSessionStatus(
  sessionId: string,
  sessionData: SessionData,
  status: SessionStatus,
  lastError: string | null = null,
) {
  sessionData.status = status;
  sessionData.lastActivityAt = Date.now();
  sessionData.lastError = lastError;
  void reportSessionStatus(sessionId, status, lastError);
}

function clearTimers(sessionData: SessionData) {
  if (sessionData.reconnectTimer) {
    clearTimeout(sessionData.reconnectTimer);
    sessionData.reconnectTimer = undefined;
  }
  if (sessionData.qrExpiryTimer) {
    clearTimeout(sessionData.qrExpiryTimer);
    sessionData.qrExpiryTimer = undefined;
  }
}

function cleanupSessionFiles(sessionId: string) {
  const sessionPath = sessionPathFor(sessionId);
  if (fs.existsSync(sessionPath)) {
    fs.rmSync(sessionPath, { recursive: true, force: true });
  }
}

function closeSocket(sessionData: SessionData, reason: string) {
  try {
    sessionData.sock.end(new Error(reason));
  } catch (err) {
    logger.debug({ err }, 'WhatsApp socket already closed');
  }
}

function expireQrIfStillPending(sessionId: string, sessionData: SessionData) {
  if (sessionData.status !== 'qr_ready') {
    return;
  }

  const message = 'QR code expired before it was scanned';
  sessionData.qr = null;
  setSessionStatus(sessionId, sessionData, 'expired', message);
  closeSocket(sessionData, message);
  sessions.delete(sessionId);
  cleanupSessionFiles(sessionId);
}

function scheduleQrExpiry(sessionId: string, sessionData: SessionData) {
  if (sessionData.qrExpiryTimer) {
    clearTimeout(sessionData.qrExpiryTimer);
  }
  sessionData.qrExpiryTimer = setTimeout(() => {
    expireQrIfStillPending(sessionId, sessionData);
  }, qrTtlMs);
}

async function startSession(sessionId: string, reconnectAttempts = 0) {
  const existing = sessions.get(sessionId);
  if (existing && !['disconnected', 'expired', 'error'].includes(existing.status)) {
    return existing;
  }
  if (existing) {
    clearTimers(existing);
    sessions.delete(sessionId);
  }

  const sessionPath = sessionPathFor(sessionId);
  const { state, saveCreds } = await useMultiFileAuthState(sessionPath);
  const { version, isLatest } = await fetchLatestBaileysVersion();
  logger.info({ sessionId, version, isLatest }, 'Starting WhatsApp session');

  const sock = makeWASocket({
    version,
    logger,
    printQRInTerminal: false,
    auth: {
      creds: state.creds,
      keys: makeCacheableSignalKeyStore(state.keys, logger),
    },
    browser: Browsers.macOS('Desktop'),
    generateHighQualityLinkPreview: true,
  });

  const sessionData: SessionData = {
    sock,
    qr: null,
    status: 'initializing',
    reconnectAttempts,
    qrAttempts: 0,
    startedAt: Date.now(),
    lastActivityAt: Date.now(),
    lastError: null,
  };
  sessions.set(sessionId, sessionData);
  setSessionStatus(sessionId, sessionData, 'initializing');

  sock.ev.on('connection.update', (update) => {
    const { connection, lastDisconnect, qr } = update;
    
    if (qr) {
      sessionData.qrAttempts += 1;
      if (sessionData.qrAttempts > maxQrAttempts) {
        const message = `QR code was regenerated more than ${maxQrAttempts} times without being scanned`;
        sessionData.qr = null;
        setSessionStatus(sessionId, sessionData, 'expired', message);
        closeSocket(sessionData, message);
        sessions.delete(sessionId);
        cleanupSessionFiles(sessionId);
        return;
      }

      sessionData.qr = qr;
      setSessionStatus(sessionId, sessionData, 'qr_ready');
      scheduleQrExpiry(sessionId, sessionData);
    }

    if (connection === 'close') {
      clearTimers(sessionData);
      const statusCode = (lastDisconnect?.error as Boom)?.output?.statusCode;
      const shouldReconnect =
        statusCode !== DisconnectReason.loggedOut &&
        sessionData.status !== 'expired' &&
        sessionData.reconnectAttempts < maxReconnectAttempts;

      logger.warn({ sessionId, shouldReconnect, statusCode }, 'WhatsApp connection closed');
      
      if (shouldReconnect) {
        setSessionStatus(sessionId, sessionData, 'disconnected', 'WhatsApp connection closed; reconnect scheduled');
        sessionData.reconnectTimer = setTimeout(() => {
          sessions.delete(sessionId);
          startSession(sessionId, sessionData.reconnectAttempts + 1).catch((err) => {
            logger.error({ err, sessionId }, 'Failed to reconnect WhatsApp session');
            setSessionStatus(sessionId, sessionData, 'error', 'Failed to reconnect WhatsApp session');
          });
        }, reconnectDelayMs);
        return;
      }

      sessions.delete(sessionId);
      if (statusCode === DisconnectReason.loggedOut) {
        cleanupSessionFiles(sessionId);
      }
      const finalStatus = sessionData.status === 'expired' ? 'expired' : 'disconnected';
      const finalError = statusCode === DisconnectReason.loggedOut
        ? 'WhatsApp session was logged out'
        : 'WhatsApp connection closed';
      setSessionStatus(sessionId, sessionData, finalStatus, finalError);
    } else if (connection === 'open') {
      clearTimers(sessionData);
      logger.info({ sessionId }, 'WhatsApp session connected successfully');
      sessionData.qr = null;
      setSessionStatus(sessionId, sessionData, 'connected');
    }
  });

  sock.ev.on('creds.update', saveCreds);

  sock.ev.on('messages.upsert', async (m) => {
    if (m.type !== 'notify') return;
    for (const msg of m.messages) {
      if (!msg.message || msg.key.fromMe) continue;
      
      const remoteJid = msg.key.remoteJid;
      const pushName = msg.pushName;
      const text = msg.message.conversation || msg.message.extendedTextMessage?.text;
      if (!text) continue;

      console.log(`Received WhatsApp message from ${pushName} (${remoteJid}): ${text}`);

      try {
        await fetch(`${backendUrl}/whatsapp/webhook/${sessionId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            remoteJid,
            pushName,
            text,
            messageId: msg.key.id,
            timestamp: msg.messageTimestamp,
          }),
        });
      } catch (err) {
        console.error('Failed to forward message to backend webhook:', err);
      }
    }
  });

  return sessionData;
}

export const initializeWhatsAppSession = async (sessionId: string) => startSession(sessionId, 0);

/**
 * On startup: scan the sessions directory and re-start any sessions that have
 * persisted auth state on disk but are no longer in the in-memory map.
 */
export const restoreExistingSessions = async (): Promise<void> => {
  if (!fs.existsSync(sessionsDir)) return;
  const entries = fs.readdirSync(sessionsDir, { withFileTypes: true });
  const sessionIds = entries
    .filter((e) => e.isDirectory())
    .map((e) => e.name);

  if (sessionIds.length === 0) {
    logger.info('No persisted WhatsApp sessions found to restore');
    return;
  }

  logger.info({ sessionIds }, `Restoring ${sessionIds.length} persisted WhatsApp session(s)`);
  await Promise.all(
    sessionIds.map((id) =>
      startSession(id, 0).catch((err) => {
        logger.error({ err, sessionId: id }, 'Failed to restore WhatsApp session on startup');
      }),
    ),
  );
};

export const getSessionStatus = (sessionId: string) => {
  const session = sessions.get(sessionId);
  if (!session) return { status: 'not_found' as const };
  return { status: session.status, qr: session.qr, last_error: session.lastError };
};

export const deleteSession = (sessionId: string) => {
  const session = sessions.get(sessionId);
  if (session) {
    clearTimers(session);
    session.sock.logout().catch((err) => {
      logger.warn({ err, sessionId }, 'Failed to logout WhatsApp session cleanly');
    });
    sessions.delete(sessionId);
  }
  cleanupSessionFiles(sessionId);
  void reportSessionStatus(sessionId, 'disconnected', 'Session deleted');
};

const waitForSessionConnected = async (sessionId: string, timeoutMs = 15000): Promise<boolean> => {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const session = sessions.get(sessionId);
    if (session && session.status === 'connected') {
      return true;
    }
    if (session && ['expired', 'error'].includes(session.status)) {
      return false;
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  return false;
};

export const sendMessage = async (sessionId: string, jid: string, text: string) => {
  let session = sessions.get(sessionId);

  // If the session is not in memory but auth state exists on disk, restore it first.
  if (!session) {
    const sessionPath = sessionPathFor(sessionId);
    if (fs.existsSync(sessionPath)) {
      logger.info({ sessionId }, 'Session not in memory; restoring from disk before sending');
      await startSession(sessionId, 0);
      session = sessions.get(sessionId);
    }
  } else if (session.status === 'disconnected') {
    logger.info({ sessionId }, 'Session disconnected; reconnecting before sending');
    await startSession(sessionId, 0);
    session = sessions.get(sessionId);
  }

  // If initializing, wait for it to connect
  if (session && session.status === 'initializing') {
    logger.info({ sessionId }, 'Session is initializing; waiting for connection before sending');
    await waitForSessionConnected(sessionId, 15000);
    session = sessions.get(sessionId);
  }

  if (!session || session.status !== 'connected') {
    throw new Error(`Session ${sessionId} is not connected (status: ${session?.status ?? 'not_found'})`);
  }

  // Ensure jid has the correct suffix
  const remoteJid = jid.includes('@') ? jid : `${jid}@s.whatsapp.net`;
  await session.sock.sendMessage(remoteJid, { text });
};
