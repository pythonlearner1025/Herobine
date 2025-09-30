/**
 * Mineflayer Bridge Server
 * Exposes Mineflayer bot via HTTP API for Python to control
 * Mimics MineStudio's action/observation interface
 */

const mineflayer = require('mineflayer')
const { Viewer } = require('prismarine-viewer').viewer
const express = require('express')
const { createCanvas, loadImage } = require('canvas')
const gl = require('gl')
const app = express()

// Make loadImage globally available for prismarine-viewer
global.loadImage = loadImage

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

// Screenshot system - module level using server-side rendering
let viewerReady = false
let serverViewer = null  // Server-side prismarine viewer
let viewerRenderer = null
let viewerWorldView = null  // Keep reference to world view for updates

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
  
  // Init server-side viewer after spawn
  bot.once('spawn', () => {
    console.log('[Bot] Spawned! Waiting for chunks to load...')
    
    // Wait for chunks to load before starting viewer  
    setTimeout(async () => {
      console.log('[Viewer] Initializing server-side renderer...')
      
      try {
        await initServerSideViewer()
      } catch (err) {
        console.error('[Viewer] Failed to initialize server-side viewer:', err.message)
        console.error('[Viewer] Stack:', err.stack)
      }
    }, 3000)  // 3 seconds for initial chunks
  })

  return bot
}

async function initServerSideViewer() {
  try {
    if (!bot || !bot.entity) {
      console.log('[Viewer] Bot or entity not ready')
      return false
    }
    
    console.log('[Viewer] Setting up server-side renderer with headless-gl...')
    const THREE = require('three')
    const Vec3 = require('vec3').Vec3
    const { WorldView } = require('prismarine-viewer').viewer
    
    const width = 640
    const height = 360
    
    // Create WebGL context using headless-gl
    console.log('[Viewer] Creating headless WebGL context...')
    const glContext = gl(width, height, { preserveDrawingBuffer: true })
    
    // Create a mock canvas element
    const mockCanvas = {
      width: width,
      height: height,
      clientWidth: width,
      clientHeight: height,
      style: {},
      addEventListener: function() {},
      removeEventListener: function() {},
      getBoundingClientRect: function() {
        return { left: 0, top: 0, width: width, height: height }
      },
      getContext: function(type) {
        if (type === 'webgl' || type === 'experimental-webgl') {
          return glContext
        }
        return null
      }
    }
    
    // Attach canvas to context
    glContext.canvas = mockCanvas
    
    // Ensure drawing buffer dimensions are set
    Object.defineProperty(glContext, 'drawingBufferWidth', {
      get: function() { return width }
    })
    Object.defineProperty(glContext, 'drawingBufferHeight', {
      get: function() { return height }
    })
    
    // Patch texImage2D to handle node-canvas Image objects
    const originalTexImage2D = glContext.texImage2D.bind(glContext)
    glContext.texImage2D = function(...args) {
      // Handle the case where we're uploading an Image
      if (args.length >= 6 && args[5] && typeof args[5] === 'object') {
        const image = args[5]
        // If it's a node-canvas Image, we need to get its raw pixel data
        if (image.width && image.height && typeof image.src !== 'undefined') {
          // Create a temporary canvas to extract pixel data
          const tempCanvas = createCanvas(image.width, image.height)
          const tempCtx = tempCanvas.getContext('2d')
          tempCtx.drawImage(image, 0, 0)
          const imageData = tempCtx.getImageData(0, 0, image.width, image.height)
          
          // Upload using the ImageData instead
          args[5] = imageData
        }
      }
      return originalTexImage2D(...args)
    }
    
    // Mock document object for THREE.js
    if (typeof document === 'undefined') {
      global.document = {
        createElement: function(tag) {
          if (tag === 'canvas') {
            return mockCanvas
          }
          if (tag === 'img') {
            // Create a proper image element for texture loading
            // Use node-canvas Image which works with headless-gl
            const { Image } = require('canvas')
            const img = new Image()
            
            // Override to handle both data URLs and file paths
            const originalSrcSetter = Object.getOwnPropertyDescriptor(Image.prototype, 'src').set
            Object.defineProperty(img, 'src', {
              set: function(value) {
                // Call original setter
                if (originalSrcSetter) {
                  originalSrcSetter.call(this, value)
                }
                
                // Also trigger onload for data URLs
                if (value && value.startsWith('data:')) {
                  setTimeout(() => {
                    if (this.onload) this.onload()
                  }, 0)
                }
              },
              get: function() {
                return this._src || ''
              }
            })
            
            return img
          }
          return {
            style: {},
            addEventListener: function() {},
            removeEventListener: function() {}
          }
        },
        createElementNS: function(ns, tag) {
          return this.createElement(tag)
        }
      }
    }
    
    console.log('[Viewer] Creating THREE.js renderer...')
    viewerRenderer = new THREE.WebGLRenderer({
      canvas: mockCanvas,
      context: glContext,
      antialias: false,
      alpha: false,
      preserveDrawingBuffer: true
    })
    
    viewerRenderer.setSize(width, height)
    
    // Set clear color to sky blue instead of black for debugging
    viewerRenderer.setClearColor(0x87CEEB, 1.0)  // Sky blue
    
    console.log('[Viewer] ✓ Renderer created with sky blue background')
    
    // Create the viewer
    console.log('[Viewer] Creating Prismarine Viewer...')
    serverViewer = new Viewer(viewerRenderer)
    serverViewer.setVersion(bot.version)
    console.log('[Viewer] ✓ Viewer created for version:', bot.version)
    
    // Configure camera clipping planes
    serverViewer.camera.near = 0.1
    serverViewer.camera.far = 1000
    serverViewer.camera.updateProjectionMatrix()
    console.log('[Viewer] ✓ Camera clip planes configured')
    
    // Add bright lighting to the scene
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.0)  // Full bright ambient
    serverViewer.scene.add(ambientLight)
    
    // Add a directional light from the sun position
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
    directionalLight.position.set(1, 1, 0.5).normalize()
    serverViewer.scene.add(directionalLight)
    
    console.log('[Viewer] ✓ Added bright lighting to scene')
    
    // Wait a bit for textures to process
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // Create world view
    const botPos = bot.entity.position
    const center = new Vec3(botPos.x, botPos.y, botPos.z)
    console.log('[Viewer] Bot position:', center)
    
    const viewDistance = 4  // Render distance in chunks
    viewerWorldView = new WorldView(bot.world, viewDistance, center)
    serverViewer.listen(viewerWorldView)
    
    console.log('[Viewer] Initializing world view (this loads chunks and textures)...')
    await viewerWorldView.init(center)
    console.log('[Viewer] ✓ World view initialized')
    
    // Check texture loading
    console.log('[Viewer] Checking textures...')
    let textureCount = 0
    let loadedTextures = 0
    serverViewer.scene.traverse(obj => {
      if (obj.material) {
        if (obj.material.map) {
          textureCount++
          if (obj.material.map.image) loadedTextures++
        }
      }
    })
    console.log('[Viewer] Textures found:', textureCount, ', with images:', loadedTextures)
    
    // Set camera position and look at the world
    serverViewer.camera.position.set(botPos.x, botPos.y + 1.6, botPos.z)
    const yaw = bot.entity.yaw || 0
    const pitch = bot.entity.pitch || 0  
    serverViewer.camera.rotation.set(pitch, yaw, 0, 'YXZ')
    
    console.log('[Viewer] Camera positioned at bot location')
    
    // Give chunks time to load and textures to upload to GPU
    console.log('[Viewer] Waiting for chunks and textures to load and upload to GPU...')
    await new Promise(resolve => setTimeout(resolve, 5000))  // Longer wait for texture upload
    
    // Debug: check what's in the scene
    console.log('[Viewer] Scene children count:', serverViewer.scene.children.length)
    console.log('[Viewer] Scene children types:', serverViewer.scene.children.map(c => c.type).join(', '))
    
    // Do a test render
    viewerRenderer.render(serverViewer.scene, serverViewer.camera)
    console.log('[Viewer] Test render complete')
    
    // Check if any meshes rendered and their materials
    let meshCount = 0
    let meshWithTexture = 0
    serverViewer.scene.traverse(obj => {
      if (obj.isMesh) {
        meshCount++
        if (obj.material && obj.material.map) meshWithTexture++
      }
    })
    console.log('[Viewer] Total meshes in scene:', meshCount)
    console.log('[Viewer] Meshes with textures:', meshWithTexture)
    
    // Check if scene has bounding box (is it visible?)
    const bbox = new THREE.Box3().setFromObject(serverViewer.scene)
    console.log('[Viewer] Scene bounding box:', {
      min: {x: bbox.min.x.toFixed(1), y: bbox.min.y.toFixed(1), z: bbox.min.z.toFixed(1)},
      max: {x: bbox.max.x.toFixed(1), y: bbox.max.y.toFixed(1), z: bbox.max.z.toFixed(1)}
    })
    
    viewerReady = true
    console.log('[Viewer] ✓✓✓ Server-side viewer FULLY INITIALIZED ✓✓✓')
    return true
    
  } catch (err) {
    console.error('[Viewer] ✗ Server-side viewer init failed:', err.message)
    console.error('[Viewer] Stack:', err.stack)
    viewerReady = false
    return false
  }
}

// Old initViewer function removed - using initServerSideViewer instead

async function captureScreenshot() {
  // Return black image if not ready
  if (!viewerReady || !serverViewer || !viewerRenderer || !bot) {
    console.log('[Viewer] Not ready for screenshot - returning black image')
    const canvas = createCanvas(640, 360)
    const ctx = canvas.getContext('2d')
    ctx.fillStyle = 'black'
    ctx.fillRect(0, 0, 640, 360)
    return canvas.toBuffer('image/jpeg')
  }
  
  try {
    // Update world view center to bot's position
    if (bot.entity && viewerWorldView) {
      const Vec3 = require('vec3').Vec3
      const botPos = bot.entity.position
      const center = new Vec3(botPos.x, botPos.y, botPos.z)
      
      // Update world view center (loads new chunks as bot moves)
      viewerWorldView.updatePosition(center)
      
      // Update camera position to bot's eye level
      serverViewer.camera.position.set(botPos.x, botPos.y + 1.6, botPos.z)
      
      // Update camera rotation based on bot's yaw and pitch
      const yaw = bot.entity.yaw
      const pitch = bot.entity.pitch
      serverViewer.camera.rotation.set(pitch, yaw, 0, 'YXZ')
    }
    
    // Render the current frame
    viewerRenderer.render(serverViewer.scene, serverViewer.camera)
    
    // Get WebGL context
    const glContext = viewerRenderer.getContext()
    const width = 640
    const height = 360
    
    // Use headless-gl's pixels() method
    let pixels
    if (typeof glContext.pixels === 'function') {
      // headless-gl specific method - returns pixels in correct format
      pixels = glContext.pixels(0, 0, width, height)
    } else {
      // Fallback to standard readPixels
      pixels = new Uint8Array(width * height * 4)
      glContext.readPixels(0, 0, width, height, glContext.RGBA, glContext.UNSIGNED_BYTE, pixels)
    }
    
    // Check if we got any data (debug - only log occasionally)
    const shouldLog = Math.random() < 0.1  // Log 10% of the time
    let nonZero = 0
    let sampleVals = []
    for (let i = 0; i < Math.min(100, pixels.length); i++) {
      if (pixels[i] !== 0) nonZero++
      if (i < 20) sampleVals.push(pixels[i])
    }
    
    if (shouldLog) {
      console.log('[Viewer] DEBUG: nonZero=', nonZero, '/100, sample:', sampleVals)
    }
    
    if (nonZero === 0 && shouldLog) {
      console.log('[Viewer] WARNING: First 100 pixels are all zero - image will be black')
    }
    
    // Create canvas and convert from RGBA to RGB
    const canvas = createCanvas(width, height)
    const ctx = canvas.getContext('2d')
    const imageData = ctx.createImageData(width, height)
    
    // headless-gl returns pixels bottom-up, need to flip Y
    for (let y = 0; y < height; y++) {
      const srcRow = height - 1 - y  // Flip Y coordinate
      for (let x = 0; x < width; x++) {
        const srcIdx = (srcRow * width + x) * 4
        const dstIdx = (y * width + x) * 4
        
        // Copy RGBA channels
        imageData.data[dstIdx] = pixels[srcIdx]      // R
        imageData.data[dstIdx + 1] = pixels[srcIdx + 1]  // G
        imageData.data[dstIdx + 2] = pixels[srcIdx + 2]  // B
        imageData.data[dstIdx + 3] = 255  // A (always opaque)
      }
    }
    
    ctx.putImageData(imageData, 0, 0)
    
    // ============ MINECRAFT-STYLE HUD OVERLAY ============
    
    // 1. CROSSHAIR (center, white with black outline for visibility)
    const centerX = width / 2
    const centerY = height / 2
    const crosshairSize = 10
    
    // Black outline
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.9)'
    ctx.lineWidth = 4
    ctx.beginPath()
    ctx.moveTo(centerX - crosshairSize, centerY)
    ctx.lineTo(centerX + crosshairSize, centerY)
    ctx.moveTo(centerX, centerY - crosshairSize)
    ctx.lineTo(centerX, centerY + crosshairSize)
    ctx.stroke()
    
    // White crosshair
    ctx.strokeStyle = 'rgba(255, 255, 255, 1.0)'
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.moveTo(centerX - crosshairSize, centerY)
    ctx.lineTo(centerX + crosshairSize, centerY)
    ctx.moveTo(centerX, centerY - crosshairSize)
    ctx.lineTo(centerX, centerY + crosshairSize)
    ctx.stroke()
    
    // 2. HOTBAR (bottom center - Minecraft style)
    const hotbarSlot = bot.quickBarSlot || 0
    const slotSize = 40
    const hotbarWidth = slotSize * 9
    const hotbarX = (width - hotbarWidth) / 2
    const hotbarY = height - 50
    
    // Draw hotbar background (dark gray with border)
    ctx.fillStyle = 'rgba(30, 30, 30, 0.8)'
    ctx.fillRect(hotbarX - 2, hotbarY - 2, hotbarWidth + 4, slotSize + 4)
    
    // Draw slot grid
    for (let i = 0; i < 9; i++) {
      const slotX = hotbarX + i * slotSize
      
      // Slot background
      if (i === hotbarSlot) {
        ctx.fillStyle = 'rgba(255, 255, 255, 0.3)'  // Highlight selected
      } else {
        ctx.fillStyle = 'rgba(60, 60, 60, 0.6)'
      }
      ctx.fillRect(slotX, hotbarY, slotSize, slotSize)
      
      // Slot border
      ctx.strokeStyle = i === hotbarSlot ? 'rgba(255, 255, 255, 1.0)' : 'rgba(139, 139, 139, 0.8)'
      ctx.lineWidth = i === hotbarSlot ? 3 : 1
      ctx.strokeRect(slotX, hotbarY, slotSize, slotSize)
      
      // Draw item name if exists
      const hotbarItem = bot.inventory.slots[36 + i]  // Hotbar starts at slot 36
      if (hotbarItem) {
        ctx.fillStyle = 'white'
        ctx.font = '10px monospace'
        const itemName = hotbarItem.name.replace('minecraft:', '').substring(0, 6)
        ctx.fillText(itemName, slotX + 2, hotbarY + slotSize - 3)
        
        // Draw count if > 1
        if (hotbarItem.count > 1) {
          ctx.fillStyle = 'white'
          ctx.font = 'bold 12px monospace'
          ctx.fillText(hotbarItem.count.toString(), slotX + slotSize - 15, hotbarY + 15)
        }
      }
    }
    
    // 3. HEALTH BAR (bottom left - Minecraft hearts style)
    const heartY = height - 60
    const maxHearts = 10
    const heartWidth = 9
    const heartSpacing = 8
    
    ctx.font = '10px monospace'
    ctx.fillStyle = 'white'
    ctx.fillText('❤', 5, heartY - 5)  // Label
    
    const hearts = Math.ceil(bot.health / 2)  // 20 health = 10 hearts
    for (let i = 0; i < maxHearts; i++) {
      const heartX = 20 + i * (heartWidth + heartSpacing)
      
      if (i < hearts) {
        ctx.fillStyle = 'rgba(255, 0, 0, 0.9)'  // Filled heart
      } else {
        ctx.fillStyle = 'rgba(100, 0, 0, 0.5)'  // Empty heart
      }
      ctx.fillRect(heartX, heartY - 8, heartWidth, 8)
    }
    
    // 4. FOOD BAR (bottom right - Minecraft drumsticks style)
    const foodY = height - 60
    const maxFood = 10
    const foodWidth = 9
    const foodSpacing = 8
    
    ctx.font = '10px monospace'
    ctx.fillStyle = 'white'
    ctx.fillText('🍗', width - 115, foodY - 5)  // Label
    
    const foodUnits = Math.ceil(bot.food / 2)  // 20 food = 10 units
    for (let i = 0; i < maxFood; i++) {
      const foodX = width - 100 + i * (foodWidth + foodSpacing)
      
      if (i < foodUnits) {
        ctx.fillStyle = 'rgba(160, 82, 45, 0.9)'  // Filled food
      } else {
        ctx.fillStyle = 'rgba(80, 40, 20, 0.5)'  // Empty food
      }
      ctx.fillRect(foodX, foodY - 8, foodWidth, 8)
    }
    
    // 5. POSITION/INFO OVERLAY (top left - for debugging)
    if (bot.entity) {
      ctx.font = '12px monospace'
      ctx.fillStyle = 'rgba(0, 0, 0, 0.7)'
      ctx.fillRect(5, 5, 200, 60)
      
      ctx.fillStyle = 'white'
      const pos = bot.entity.position
      ctx.fillText(`Pos: ${pos.x.toFixed(1)}, ${pos.y.toFixed(1)}, ${pos.z.toFixed(1)}`, 10, 20)
      ctx.fillText(`Health: ${bot.health}/20`, 10, 35)
      ctx.fillText(`Food: ${bot.food}/20`, 10, 50)
    }
    
    console.log('[Viewer] Screenshot captured successfully')
    return canvas.toBuffer('image/jpeg', { quality: 0.9 })
    
  } catch (err) {
    console.error('[Viewer] Screenshot error:', err.message)
    console.error('[Viewer] Stack:', err.stack)
    
    // Return black image on error
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
      height: 360,
      viewerReady: viewerReady
    })
  } catch (err) {
    res.json({ success: false, error: err.message })
  }
})

// Viewer status endpoint
app.get('/viewer/status', (req, res) => {
  res.json({
    success: true,
    viewerReady: viewerReady,
    serverViewer: serverViewer !== null,
    viewerRenderer: viewerRenderer !== null,
    botConnected: bot && bot.entity !== null
  })
})

const PORT = process.env.MINEFLAYER_PORT || 1111
app.listen(PORT, () => {
  console.log(`[Bridge] Mineflayer bridge server running on port ${PORT}`)
})

