# Hot LapY 🏁

A realistic 2D time trial racing game with advanced automotive physics, built with Python and Pygame. Master the art of racing with authentic car behavior, realistic transmission systems, and immersive engine audio!

## 🎮 Game Description

Hot LapY is a sophisticated 2D top-down racing simulator that goes beyond simple arcade racing. Featuring realistic car physics, a 5-speed manual transmission system, RPM-based engine simulation, and gear-dependent audio, this game provides an authentic racing experience where every input matters.

## ✨ Key Features

### 🚗 **Realistic Car Physics**
- **Authentic Engine Simulation**: Torque curves, horsepower, and RPM-based power delivery
- **5-Speed Manual Transmission**: Realistic gear ratios from 3.5:1 (1st) to 0.8:1 (5th overdrive)
- **Advanced Traction System**: Speed-dependent grip loss and tire physics
- **Engine Braking**: Gear-dependent deceleration when off throttle
- **Realistic Acceleration**: Progressive power delivery based on RPM and gear

### 🔧 **Transmission System**
- **Manual Gear Control**: Use Q/E to shift up/down through 5 forward gears + reverse
- **Gear-Specific Performance**: Each gear has optimal speed ranges and power characteristics
- **Automatic Clutch**: Simplified operation while maintaining realistic gear behavior
- **Rev Limiter**: Engine protection at 6000 RPM redline

### 🔊 **Dynamic Audio System**
- **RPM-Based Engine Sound**: Audio pitch tied to actual engine RPM, not speed
- **Gear-Dependent Audio**: Each gear has distinct sound characteristics
- **Realistic Volume Control**: Engine volume responds to throttle input and RPM
- **Collision Sound Effects**: Audio feedback for wall impacts

### � **Racing Features**
- **Checkpoint System**: Valid lap completion requires passing all checkpoints in sequence
- **Precision Lap Timing**: Millisecond-accurate timing system
- **Best Lap Tracking**: Automatic personal best recording
- **Real-Time Telemetry**: Live display of speed, gear, RPM, and lap information

### 🎯 **Advanced Collision System**
- **Wall Collision Detection**: Realistic bounce-back from track boundaries
- **Screen Boundary Protection**: Prevents car from leaving play area
- **Collision Audio**: Sound effects for impact feedback

## 🕹️ Controls

### **Driving Controls**
- **W / ↑** - Accelerate (throttle)
- **S / ↓** - Brake/Reverse
- **A / ←** - Steer left
- **D / →** - Steer right

### **Transmission Controls**
- **Q** - Shift down (gear-)
- **E** - Shift up (gear+)

### **Game Controls**
- **R** - Reset car to starting position
- **ESC** - Exit game

## 📊 Real-Time Display

The game provides comprehensive real-time information:
- **Current Speed**: Displayed in game units
- **Current Gear**: Shows active gear (R, N, 1-5)
- **Engine RPM**: Live tachometer reading
- **Current Lap Time**: Running stopwatch
- **Best Lap Time**: Your personal record
- **Lap Counter**: Total completed laps

## 🛠️ Technical Specifications

### **Physics Engine**
```python
# Realistic automotive constants
MAX_RPM = 6000               # Redline
IDLE_RPM = 800              # Engine idle
ENGINE_TORQUE_MAX = 100     # Peak torque (Nm)
ENGINE_POWER_MAX = 150      # Peak power (HP)
OPTIMAL_RPM = 3500          # Power peak

# Transmission ratios
GEAR_RATIOS = {
    1: 3.5,  # First gear (high torque)
    2: 2.1,  # Second gear
    3: 1.4,  # Third gear
    4: 1.0,  # Fourth gear (1:1)
    5: 0.8   # Fifth gear (overdrive)
}
```

### **Advanced Features**
- **Gear-Dependent Engine Braking**: Lower gears provide stronger deceleration
- **Speed-Dependent Steering**: Realistic steering response at different speeds
- **Traction Loss Simulation**: Grip reduction at high speeds
- **RPM-Matched Audio**: Engine sound pitch changes with actual RPM and gear

## 🚀 Installation & Setup

### **Prerequisites**
- Python 3.7+
- Pygame library

### **Installation Steps**

1. **Clone the repository**
   ```bash
   git clone https://github.com/DoToMaSi/hotlap-Py.git
   cd hotlap-Py
   ```

2. **Install dependencies**
   ```bash
   pip install pygame
   ```

3. **Ensure asset files are present**
   ```
   assets/
   ├── track.png    # Track image
   ├── car.png      # Car sprite
   ├── car.wav      # Engine sound
   └── crash.wav    # Collision sound
   ```

4. **Run the game**
   ```bash
   python hot_lap.py
   ```

## 🏎️ Driving Tips

### **Mastering the Transmission**
- **1st Gear**: Use for acceleration from standstill and tight corners
- **2nd-3rd Gear**: Optimal for most corner exits and mid-speed sections
- **4th Gear**: Balanced gear for general driving
- **5th Gear**: Use on straights for maximum top speed

### **Racing Techniques**
- **Brake Before Corners**: Use engine braking by downshifting
- **Smooth Inputs**: Gradual throttle and steering for better traction
- **Gear Selection**: Choose appropriate gear for corner speed
- **Racing Line**: Follow optimal path through checkpoints

### **Performance Optimization**
- **Shift Points**: Shift up around 5500-6000 RPM for maximum power
- **Cornering**: Downshift before corners for better control
- **Throttle Control**: Modulate throttle for traction in corners

## 🏁 Game Modes

- **Time Trial**: Race against the clock to set your best lap time
- **Practice**: Free driving to learn the track and perfect your technique
- **Hot Lap Challenge**: Push the limits for the ultimate lap time

## 📈 System Architecture

### **Object-Oriented Design**
- **Car Class**: Complete vehicle simulation with physics and transmission
- **Track Class**: Circuit layout with checkpoints and collision detection
- **AudioManager Class**: Advanced sound system with RPM-based pitch shifting
- **GameUI Class**: Real-time information display system
- **LapTimer Class**: Precision timing and lap validation

### **Modular Components**
- Separated physics engine from rendering
- Independent audio system with fallback options
- Scalable UI system for additional information display

## 🎵 Audio Features

The game features an advanced audio system that simulates realistic engine sounds:
- **RPM-Synchronized**: Engine pitch changes with actual RPM
- **Gear-Dependent Characteristics**: Different sound profile per gear
- **Dynamic Volume**: Responds to throttle input and engine load
- **Collision Feedback**: Audio cues for track contact

## 🔧 Customization

The game is designed for easy modification:
- **Physics Constants**: Easily adjustable in the constants section
- **Gear Ratios**: Customizable transmission characteristics  
- **Track Layout**: Modifiable checkpoint and wall positions
- **Audio Settings**: Configurable pitch ranges and volume levels

## 🏆 Performance Metrics

Track your progress with detailed statistics:
- **Lap Times**: Precise timing to the millisecond
- **Speed Records**: Monitor top speeds achieved
- **Gear Usage**: Analyze transmission efficiency
- **Consistency**: Track lap time variations

---

## 🚀 Future Enhancements

Potential additions for expanded gameplay:
- Multiple track layouts
- Weather effects and tire compounds  
- Telemetry data logging
- Ghost car for time comparisons
- Advanced setup options (gear ratios, differential)

---

**Challenge yourself to master the perfect lap! 🏁**

*"In racing, everything that is not going forward is going backward." - Racing Philosophy*

## 📄 License

This project is open source. Feel free to modify and distribute according to your needs.

## 🤝 Contributing

Contributions are welcome! Whether it's new features, bug fixes, or track designs, feel free to submit pull requests or open issues.

---

*Built with passion for realistic racing simulation* ❤️🏎️