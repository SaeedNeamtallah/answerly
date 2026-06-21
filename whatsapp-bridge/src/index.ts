import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { initializeWhatsAppSession, getSessionStatus, deleteSession, sendMessage, restoreExistingSessions } from './whatsappClient';

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 3002;

app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'whatsapp-bridge' });
});

app.post('/api/sessions/:sessionId', async (req, res) => {
  const { sessionId } = req.params;
  try {
    await initializeWhatsAppSession(sessionId);
    res.json({ success: true, message: `Session ${sessionId} initialized` });
  } catch (error) {
    res.status(500).json({ success: false, error: 'Failed to initialize session' });
  }
});

app.get('/api/sessions/:sessionId/status', (req, res) => {
  const { sessionId } = req.params;
  const status = getSessionStatus(sessionId);
  res.json(status);
});

app.delete('/api/sessions/:sessionId', (req, res) => {
  const { sessionId } = req.params;
  deleteSession(sessionId);
  res.json({ success: true, message: `Session ${sessionId} deleted` });
});

app.post('/api/sessions/:sessionId/send', async (req, res) => {
  const { sessionId } = req.params;
  const { jid, text } = req.body;
  if (!jid || !text) {
    return res.status(400).json({ success: false, error: 'Missing jid or text in request body' });
  }
  try {
    await sendMessage(sessionId, jid, text);
    res.json({ success: true, message: 'Message sent' });
  } catch (error: any) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.listen(PORT, async () => {
  console.log(`WhatsApp Bridge running on port ${PORT}`);
  // Restore any sessions that were persisted to disk before this process started.
  await restoreExistingSessions();
});
