# 🚀 START HERE - MineRL Server Quick Reference

**You are now in the MineRL server directory.**  
**All MineRL logic is here, separate from `/workspace/Herobine/bridge/` (old Mineflayer system).**

---

## 🎯 Quick Commands

### 1️⃣ Test Hands Visibility (30 seconds)

```bash
python test_hands.py
```

**Expected:** `✓✓✓ HANDS LIKELY VISIBLE! ✓✓✓`

---

### 2️⃣ Run Agent (Basic)

```bash
# Make sure VLLM is running:
# cd /workspace/Herobine && ./start_vllm_server.sh

python server_minerl.py \
  --checkpoint /path/to/jarvis_vla_qwen2_vl_7b_sft \
  --instruction "Mine stone" \
  --max-steps 200
```

---

### 3️⃣ Run Agent with Interactive Mode 🎮

**This allows YOU to connect your Minecraft client and watch the agent play in real-time!**

**On server:**
```bash
python server_minerl.py \
  --checkpoint /path/to/model \
  --interactive-port 6666 \
  --instruction "Build a house"
```

**On your local computer (Terminal 1):**
```bash
ssh -L 6666:localhost:6666 user@server-ip
# Keep this open!
```

**On your local computer (Terminal 2):**
```bash
pip install minestudio
python3 -m minestudio.simulator.minerl.interactor 6666 --ip localhost
```

**A Minecraft window opens - you're watching the agent!**

To become invisible: Press `t`, type `/gamemode sp`, press Enter

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| **START_HERE.md** | This file - quick commands |
| **README.md** | Overview and examples |
| **SETUP.md** | Complete setup guide with troubleshooting |
| **MIGRATION_COMPLETE.md** | Technical details of migration |

---

## ✅ System Requirements Verified

- ✅ Java 8 (OpenJDK 1.8.0_462)
- ✅ MineStudio with MineRL
- ✅ Python 3.10+
- ✅ VLLM server ready

**All requirements met - ready to run!**

---

## 🔑 Key Features

✅ **Proper POV with hands** (unlike old mineflayer system)  
✅ **Real Minecraft HUD** (not fake overlays)  
✅ **Interactive mode** (humans can spectate/interact)  
✅ **GUI screens work** (inventory, chests)  
✅ **Distribution match** (for VLA training data)  

---

## 🆚 vs Old Mineflayer System

| Feature | Mineflayer (`/bridge/`) | MineRL (HERE) |
|---------|------------------------|---------------|
| Hands | ❌ No | ✅ **YES** |
| HUD | Fake | Real |
| Interactive | No | **Yes!** |
| MC Version | 1.21.8 | 1.16.5 |

**Old system preserved at:** `/workspace/Herobine/bridge/`

---

## 🐛 Common Issues

**"Cannot connect to X server"**
```bash
xvfb-run -a python server_minerl.py ...
```

**"Interactor connection failed"**
```bash
# Make sure server is running FIRST, then connect
# Check port forwarding: netstat -an | grep 6666
```

**"Hands not visible"**
```bash
# This shouldn't happen! Run:
python test_hands.py
# And check the screenshot
```

See **SETUP.md** for detailed troubleshooting.

---

## 🎓 Learn More

**Why we migrated from prismarine-viewer:**  
See `/workspace/Herobine/bridge/CONTEXT_SUMMARY.md` for the full technical analysis.

**MineRL interactive mode docs:**  
https://minerl.readthedocs.io/en/latest/tutorials/index.html

---

## 📞 Next Steps

1. **Test:** `python test_hands.py`
2. **Run:** `python server_minerl.py --checkpoint <path> --instruction "Mine stone"`
3. **Watch:** Set up interactive mode and spectate!

---

**Your agent now has proper first-person vision and you can watch it play in real-time!** 🎮

