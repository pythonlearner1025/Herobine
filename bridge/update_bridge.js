// Run this script to add chat and screenshot support to mineflayer_bridge.js
// Usage: node update_bridge.js

const fs = require('fs');

const chatAndScreenshotCode = `
// ===== Chat Instruction System =====
let chatInstructions = []
let processingInstruction = null

bot.on('chat', (username, message) => {
  if (username === bot.username) return  // Ignore self
  
  console.log(\`[Chat] \${username}: \${message}\`)
  
  // Handle reset
  if (message.toLowerCase().trim() === 'reset') {
    console.log('[Chat] Reset command')
    processingInstruction = null
    chatInstructions = []
    return
  }
  
  // Queue new instruction
  chatInstructions.push({
    username: username,
    message: message,
    timestamp: Date.now()
  })
  console.log(\`[Chat] Queued: "\${message}"\`)
})

// ===== Screenshot System =====
let viewerReady = false
let viewer = null

async function initViewer() {
  if (!bot || !bot.entity) return false
  
  try {
    const { Viewer, WorldView } = require('prismarine-viewer').viewer
    const THREE = require('three')
    const { createCanvas } = require('canvas')
    const Vec3 = require('vec3').Vec3
    
    const width = 640, height = 360
    const canvas = createCanvas(width, height)
    const renderer = new THREE.WebGLRenderer({ canvas: canvas })
    
    viewer = {
      viewer: new Viewer(renderer),
      canvas: canvas,
      renderer: renderer,
      width: width,
      height: height
    }
    
    viewer.viewer.setVersion(bot.version)
    
    const botPos = bot.entity.position
    const center = new Vec3(botPos.x, botPos.y, botPos.z)
    
    const worldView = new WorldView(bot.world, 4, center)
    viewer.viewer.listen(worldView)
    viewer.worldView = worldView
    
    await worldView.init(center)
    viewerReady = true
    console.log('[Viewer] Screenshot support ready')
    return true
  } catch (err) {
    console.error('[Viewer] Init failed:', err.message)
    return false
  }
}

async function captureScreenshot() {
  if (!viewerReady || !viewer || !bot || !bot.entity) {
    // Black image fallback
    const canvas = createCanvas(640, 360)
    const ctx = canvas.getContext('2d')
    ctx.fillStyle = 'black'
    ctx.fillRect(0, 0, 640, 360)
    return canvas.toBuffer('image/jpeg')
  }
  
  try {
    const pos = bot.entity.position
    viewer.viewer.camera.position.set(pos.x, pos.y + 1.6, pos.z)
    
    // Convert yaw/pitch to look direction
    const yaw = bot.entity.yaw
    const pitch = bot.entity.pitch
    
    const x = -Math.sin(yaw) * Math.cos(pitch)
    const y = -Math.sin(pitch)
    const z = -Math.cos(yaw) * Math.cos(pitch)
    
    const Vec3 = require('vec3').Vec3
    const lookAt = new Vec3(pos.x + x, pos.y + 1.6 + y, pos.z + z)
    
    viewer.viewer.camera.lookAt(lookAt.x, lookAt.y, lookAt.z)
    viewer.renderer.render(viewer.viewer.scene, viewer.viewer.camera)
    
    return viewer.canvas.toBuffer('image/jpeg')
  } catch (err) {
    console.error('[Viewer] Screenshot failed:', err.message)
    const canvas = createCanvas(640, 360)
    const ctx = canvas.getContext('2d')
    ctx.fillStyle = 'black'
    ctx.fillRect(0, 0, 640, 360)
    return canvas.toBuffer('image/jpeg')
  }
}

// Init viewer after spawn
bot.on('spawn', async () => {
  setTimeout(() => initViewer(), 2000)
})
`;

const chatEndpoints = `
// Chat endpoints
app.post('/chat/instructions', (req, res) => {
  res.json({
    success: true,
    instructions: chatInstructions,
    current: processingInstruction
  })
})

app.post('/chat/start_instruction', (req, res) => {
  if (chatInstructions.length > 0) {
    processingInstruction = chatInstructions.shift()
    res.json({ success: true, instruction: processingInstruction })
  } else {
    res.json({ success: true, instruction: null })
  }
})

app.post('/chat/clear_instruction', (req, res) => {
  processingInstruction = null
  res.json({ success: true })
})

// Screenshot endpoint
app.post('/screenshot', async (req, res) => {
  if (!bot) {
    return res.json({ success: false, error: 'Bot not initialized' })
  }
  
  try {
    const imageBuffer = await captureScreenshot()
    const base64Image = imageBuffer.toString('base64')
    
    res.json({
      success: true,
      image: base64Image,
      format: 'jpeg',
      width: 640,
      height: 360
    })
  } catch (err) {
    res.json({ success: false, error: err.message })
  }
})
`;

console.log('Reading mineflayer_bridge.js...');
let content = fs.readFileSync('mineflayer_bridge.js', 'utf8');

// Find where to insert chat code (after bot creation)
const insertAfterBotEnd = content.indexOf("  return bot\n}");
if (insertAfterBotEnd !== -1) {
  const insertPos = content.indexOf('\n', insertAfterBotEnd) + 1;
  content = content.slice(0, insertPos) + chatAndScreenshotCode + content.slice(insertPos);
  console.log('✓ Added chat listener and screenshot system');
} else {
  console.log('✗ Could not find insertion point for chat/screenshot code');
  process.exit(1);
}

// Find where to insert endpoints (before app.listen)
const listenPos = content.indexOf('const PORT =');
if (listenPos !== -1) {
  content = content.slice(0, listenPos) + chatEndpoints + '\n' + content.slice(listenPos);
  console.log('✓ Added chat and screenshot endpoints');
} else {
  console.log('✗ Could not find insertion point for endpoints');
  process.exit(1);
}

// Backup original
fs.writeFileSync('mineflayer_bridge.js.backup2', fs.readFileSync('mineflayer_bridge.js'));
console.log('✓ Backed up original to mineflayer_bridge.js.backup2');

// Write updated file
fs.writeFileSync('mineflayer_bridge.js', content);
console.log('✓ Updated mineflayer_bridge.js');
console.log('');
console.log('All changes applied successfully!');
console.log('Test with: python server_mineflayer.py --mc-host 2.tcp.us-cal-1.ngrok.io --mc-port 19335');



