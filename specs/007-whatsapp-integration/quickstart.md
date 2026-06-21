# Quickstart: WhatsApp Integration

## Running Locally

1. **Install Node.js Dependencies**:
   ```bash
   cd whatsapp-bridge
   npm install
   ```

2. **Start the Bridge**:
   ```bash
   npm run dev
   ```
   The bridge will start on port `3002` (or configured).

3. **Backend Configuration**:
   Ensure your `.env` has the bridge URL:
   ```env
   WHATSAPP_BRIDGE_URL=http://localhost:3002
   ```

4. **Add a WhatsApp Bot**:
   - Go to `http://localhost:3001/whatsapp-bots`
   - Click "New Bot"
   - A QR Code will be generated. Scan it with the WhatsApp app on your phone (Linked Devices -> Link a Device).
   - The status will change to "Active".
   - You can now send messages to that WhatsApp number and the RAG pipeline will reply!
