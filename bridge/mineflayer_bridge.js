/**
 * Mineflayer Bridge Server
 * Exposes Mineflayer bot via HTTP API for Python to control
 * Mimics MineStudio's action/observation interface
 */

const mineflayer = require('mineflayer')
const express = require('express')
const { createCanvas } = require('canvas')
const app = express()

app.use(express.json({ limit: '50mb' }))

let bot = null
let currentObservation = null
let serverConfig = {
  host: 'localhost',
  port: 25565,
  username: 'AIBot'
}

// Chat instruction system - module level
let chatInstructions = []
let processingInstruction = null

// Screenshot system - module level  
let viewerReady = false
let viewer = null

// Initialize bot
function createBot(config) {
  if (bot) {
    bot.end()
  }
  
  bot = mineflayer.createBot({
    host: config.host || serverConfig.host,
    port: config.port || serverConfig.port,
    username: config.username || serverConfig.username,
    version: config.version || false, // Auto-detect
    auth: config.auth || 'offline'
  })

  bot.on('login', () => {
    console.log('[Bot] Logged in to server')
  })

  bot.on('spawn', () => {
    console.log('[Bot] Spawned in world')
  })

  bot.on('error', (err) => {
    console.error('[Bot] Error:', err)
  })

  bot.on('kicked', (reason) => {
    console.log('[Bot] Kicked:', reason)
  })

  bot.on('end', () => {
    console.log('[Bot] Disconnected')
  })

  // Setup chat listener when bot is created
  bot.on('chat', (username, message) => {
    if (username === bot.username) return  // Ignore self
    
    console.log(`[Chat] ${username}: ${message}`)
    
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
    console.log(`[Chat] Queued: "${message}"`)
  })
  
  // Init viewer after spawn
  bot.on('spawn', async () => {
    setTimeout(() => initViewer(), 2000)
  })

  return bot
}

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

// Get current observation (screenshot + state)
async function getObservation() {
  if (!bot) return null
  
  const obs = {
    // Position
    position: bot.entity ? {
      x: bot.entity.position.x,
      y: bot.entity.position.y,
      z: bot.entity.position.z
    } : null,
    
    // Rotation (yaw, pitch)
    yaw: bot.entity ? bot.entity.yaw : 0,
    pitch: bot.entity ? bot.entity.pitch : 0,
    
    // Health/Food
    health: bot.health || 0,
    food: bot.food || 0,
    
    // Inventory (simplified)
    inventory: bot.inventory.items().map(item => ({
      name: item.name,
      count: item.count,
      slot: item.slot
    })),
    
    // Nearby entities
    entities: Object.values(bot.entities).filter(e => 
      e.position && bot.entity && 
      e.position.distanceTo(bot.entity.position) < 32
    ).map(e => ({
      type: e.name,
      position: { x: e.position.x, y: e.position.y, z: e.position.z },
      distance: bot.entity ? e.position.distanceTo(bot.entity.position) : null
    })),
    
    // Time
    time: bot.time.timeOfDay || 0,
    
    // Game mode
    gameMode: bot.game.gameMode || 'survival'
  }
  
  return obs
}

// Execute action (MineStudio-like)
async function executeAction(action) {
  if (!bot) {
    return { success: false, error: 'Bot not initialized' }
  }

  try {
    // Handle different action types
    const { type, ...params } = action

    switch (type) {
      case 'forward':
        bot.setControlState('forward', params.value || true)
        setTimeout(() => bot.setControlState('forward', false), params.duration || 100)
        break
      
      case 'back':
        bot.setControlState('back', params.value || true)
        setTimeout(() => bot.setControlState('back', false), params.duration || 100)
        break
      
      case 'left':
        bot.setControlState('left', params.value || true)
        setTimeout(() => bot.setControlState('left', false), params.duration || 100)
        break
      
      case 'right':
        bot.setControlState('right', params.value || true)
        setTimeout(() => bot.setControlState('right', false), params.duration || 100)
        break
      
      case 'jump':
        bot.setControlState('jump', true)
        setTimeout(() => bot.setControlState('jump', false), params.duration || 100)
        break
      
      case 'sneak':
        bot.setControlState('sneak', params.value || true)
        break
      
      case 'sprint':
        bot.setControlState('sprint', params.value || true)
        break
      
      case 'attack':
        if (bot.entity && bot.nearestEntity) {
          await bot.attack(bot.nearestEntity())
        }
        break
      
      case 'use':
        bot.activateItem()
        break
      
      case 'look':
        if (params.yaw !== undefined) bot.look(params.yaw, params.pitch || 0, true)
        break
      
      case 'chat':
        bot.chat(params.message || '')
        break
      
      case 'noop':
        // Do nothing
        break
      
      default:
        return { success: false, error: `Unknown action type: ${type}` }
    }

    return { success: true }
  } catch (error) {
    return { success: false, error: error.message }
  }
}

// API Endpoints

app.post('/init', async (req, res) => {
  try {
    const config = req.body
    createBot(config)
    res.json({ success: true, message: 'Bot initialized' })
  } catch (error) {
    res.status(500).json({ success: false, error: error.message })
  }
})

app.get('/observation', async (req, res) => {
  try {
    const obs = await getObservation()
    res.json({ success: true, observation: obs })
  } catch (error) {
    res.status(500).json({ success: false, error: error.message })
  }
})

app.post('/action', async (req, res) => {
  try {
    const action = req.body
    const result = await executeAction(action)
    const obs = await getObservation()
    res.json({ ...result, observation: obs })
  } catch (error) {
    res.status(500).json({ success: false, error: error.message })
  }
})

app.post('/reset', async (req, res) => {
  try {
    // Respawn or recreate bot
    if (bot) {
      bot.chat('/kill @s')
      await new Promise(resolve => setTimeout(resolve, 1000))
    } else {
      createBot(req.body || {})
      await new Promise(resolve => {
        bot.once('spawn', resolve)
        setTimeout(resolve, 5000) // Timeout
      })
    }
    const obs = await getObservation()
    res.json({ success: true, observation: obs })
  } catch (error) {
    res.status(500).json({ success: false, error: error.message })
  }
})

app.post('/close', async (req, res) => {
  try {
    if (bot) {
      bot.end()
      bot = null
    }
    res.json({ success: true })
  } catch (error) {
    res.status(500).json({ success: false, error: error.message })
  }
})

app.get('/status', (req, res) => {
  res.json({
    success: true,
    connected: bot && bot.entity !== null,
    username: bot ? bot.username : null
  })
})


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

const PORT = process.env.MINEFLAYER_PORT || 3333
app.listen(PORT, () => {
  console.log(`[Bridge] Mineflayer bridge server running on port ${PORT}`)
})

