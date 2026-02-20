# 🌐 SDARS Web Dashboard

Beautiful, modern web interface for the SDARS disaster prediction system.

## ✨ Features

- 🎨 **Premium Dark Mode Design** - Glassmorphism effects and smooth animations
- 🗺️ **Quick Location Selection** - Pre-configured major cities
- 📍 **Custom Coordinates** - Enter any latitude/longitude
- 📊 **Real-Time Predictions** - Fire, Flood, and Cyclone risk analysis
- 🤖 **AI Reasoning** - See why each prediction was made
- 📈 **Contribution Analysis** - Satellite vs Weather data breakdown
- 🌡️ **Weather Display** - Current conditions for analyzed location

## 🚀 How to Use

### Step 1: Start the Backend API

```bash
cd backend
python api/server.py
```

The API will start at: `http://localhost:8000`

### Step 2: Open the Dashboard

Simply open `index.html` in your web browser:
- Double-click `index.html`, OR
- Right-click → Open with → Your browser

### Step 3: Analyze Locations

1. **Quick Selection**: Click any city button (Mumbai, Chennai, etc.)
2. **Custom Location**: Enter latitude, longitude, and name
3. **View Results**: See AI predictions with detailed reasoning!

## 📋 Features Overview

### Location Analysis
- Click pre-configured city buttons for instant analysis
- Or enter custom coordinates for any location worldwide
- Real-time connection to AI backend

### Disaster Predictions
Each disaster type shows:
- **Risk Level**: LOW / MEDIUM / HIGH
- **Confidence Score**: 0-100%
- **AI Reasoning**: Why the prediction was made
- **Data Contributions**: How much came from satellite vs weather

### Visual Indicators
- 🔥 **Fire Risk** - Red theme, thermal & weather analysis
- 🌊 **Flood Risk** - Blue theme, rainfall & water detection  
- 🌪️ **Cyclone Risk** - Purple theme, pressure & wind analysis

## 🎨 Design Features

- **Dark Mode**: Easy on the eyes with premium aesthetics
- **Glassmorphism**: Frosted glass effect on cards
- **Gradients**: Beautiful color transitions
- **Animations**: Smooth hover effects and transitions
- **Responsive**: Works on desktop, tablet, and mobile
- **Modern Fonts**: Inter font family loaded from Google Fonts

## 🔧 Technology Stack

- **HTML5**: Semantic markup
- **CSS3**: Modern styling with CSS variables
- **JavaScript (Vanilla)**: No frameworks needed
- **Fetch API**: Connects to FastAPI backend
- **Responsive Grid**: CSS Grid for layouts

## 📡 API Integration

The dashboard connects to your FastAPI backend:

```javascript
POST http://localhost:8000/api/predict
{
  "lat": 19.0760,
  "lon": 72.8777,
  "name": "Mumbai"
}
```

Returns comprehensive disaster predictions with reasoning.

## 🎯 What Makes It Premium

✅ **Dark Theme** - Modern, professional look
✅ **Glassmorphism** - Trendy frosted glass effects
✅ **Smooth Animations** - Micro-interactions on hover
✅ **Color Theory** - Carefully chosen color palette
✅ **Typography** - Premium Inter font
✅ **Responsive** - Works on all screen sizes
✅ **Loading States** - User feedback during API calls
✅ **Error Handling** - Graceful error messages

## 🚨 Troubleshooting

**Dashboard shows "Error connecting to API"**
- Make sure backend is running: `python backend/api/server.py`
- Check console for CORS errors
- Verify API is at http://localhost:8000

**Nothing happens when clicking analyze**
- Open browser developer console (F12)
- Check for JavaScript errors
- Ensure backend API is running

**Predictions not showing**
- API might need OpenWeather API key for real data
- Check backend/.env file
- Or use demo mode without keys (limited)

## 📸 Screenshots

The dashboard features:
1. Hero section with gradient title
2. Location selection buttons
3. Custom coordinate input
4. Three risk cards (Fire, Flood, Cyclone)
5. Weather conditions display
6. How it works section

## 🔮 Future Enhancements

- [ ] Interactive map with pins
- [ ] Historical data charts
- [ ] Real-time alerts/notifications
- [ ] Multiple location comparison
- [ ] Export reports as PDF
- [ ] Dark/Light theme toggle
- [ ] Mobile app (React Native)

## 📄 Files

- `index.html` - Main HTML structure
- `styles.css` - All styling and animations
- `script.js` - JavaScript for API integration

## 💡 Tips

- Try different locations to see varying predictions
- Watch how satellite vs weather contributions change
- Notice how rapid weather changes affect predictions
- Check the reasoning to understand AI decision-making

---

**Built with ❤️ for disaster prevention**

Perfect for presentations and demonstrations!
