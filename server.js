const express = require('express');
const cors = require('cors');
const Groq = require('groq-sdk');
const path = require('path');
const crypto = require('crypto');

require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'frontend')));

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

// In-memory user store (use a database in production)
const users = new Map();

// Simple hash function
function hashPassword(password, salt) {
  return crypto.pbkdf2Sync(password, salt, 1000, 64, 'sha256').toString('hex');
}

function generateToken() {
  return crypto.randomBytes(32).toString('hex');
}

// Auth middleware
function authMiddleware(req, res, next) {
  const token = req.headers.authorization?.replace('Bearer ', '') || req.headers['x-auth-token'];
  if (!token) {
    return res.status(401).json({ success: false, error: 'Authentication required' });
  }
  const user = users.get(token);
  if (!user) {
    return res.status(401).json({ success: false, error: 'Invalid or expired token' });
  }
  req.user = user;
  next();
}

// Register endpoint
app.post('/api/register', (req, res) => {
  try {
    const { name, email, password } = req.body;

    if (!name || !email || !password) {
      return res.status(400).json({ success: false, error: 'All fields are required' });
    }

    if (password.length < 6) {
      return res.status(400).json({ success: false, error: 'Password must be at least 6 characters' });
    }

    // Check if user already exists
    for (const [token, user] of users) {
      if (user.email === email.toLowerCase()) {
        return res.status(400).json({ success: false, error: 'Email already registered' });
      }
    }

    const salt = crypto.randomBytes(16);
    const hashedPassword = hashPassword(password, salt);
    const token = generateToken();

    users.set(token, {
      id: crypto.randomUUID(),
      name,
      email: email.toLowerCase(),
      password: hashedPassword,
      salt: salt.toString('hex'),
      createdAt: new Date().toISOString()
    });

    res.json({
      success: true,
      data: { message: 'Registration successful' }
    });
  } catch (error) {
    console.error('Registration error:', error);
    res.status(500).json({ success: false, error: 'Registration failed' });
  }
});

// Login endpoint
app.post('/api/login', (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ success: false, error: 'Email and password are required' });
    }

    let foundUser = null;
    let foundToken = null;

    for (const [token, user] of users) {
      if (user.email === email.toLowerCase()) {
        foundUser = user;
        foundToken = token;
        break;
      }
    }

    if (!foundUser) {
      return res.status(401).json({ success: false, error: 'Invalid email or password' });
    }

    const hashedPassword = hashPassword(password, Buffer.from(foundUser.salt, 'hex'));

    if (hashedPassword !== foundUser.password) {
      return res.status(401).json({ success: false, error: 'Invalid email or password' });
    }

    const newToken = generateToken();
    users.set(newToken, { ...foundUser });
    users.delete(foundToken);

    res.json({
      success: true,
      data: {
        token: newToken,
        user: { id: foundUser.id, name: foundUser.name, email: foundUser.email }
      }
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ success: false, error: 'Login failed' });
  }
});

// Chat endpoint (protected)
app.post('/api/chat', authMiddleware, async (req, res) => {
  try {
    const { message, session_id } = req.body;

    if (!message) {
      return res.status(400).json({
        success: false,
        error: 'Message is required'
      });
    }

    const response = await groq.chat.completions.create({
      model: 'llama-3.3-70b-versatile',
      messages: [
        { role: 'system', content: 'You are a helpful AI assistant. Be concise and friendly.' },
        { role: 'user', content: message }
      ],
      max_tokens: 500,
      temperature: 0.7
    });

    const aiResponse = response.choices[0].message.content;

    res.json({
      success: true,
      data: {
        session_id: session_id || `session_${Date.now()}`,
        response: aiResponse,
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'Serverless AI Chatbot',
    groq_configured: !!process.env.GROQ_API_KEY
  });
});

// Auth check endpoint
app.get('/api/me', authMiddleware, (req, res) => {
  res.json({
    success: true,
    data: {
      user: { id: req.user.id, name: req.user.name, email: req.user.email }
    }
  });
});

// Serve login page as default
app.get('/login', (req, res) => {
  res.sendFile(path.join(__dirname, 'frontend', 'login.html'));
});

// Serve chat page (protected)
app.get('/chat', (req, res) => {
  res.sendFile(path.join(__dirname, 'frontend', 'index.html'));
});

// Serve frontend
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'frontend', 'login.html'));
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`🤖 Server running on port ${PORT}`);
});

module.exports = app;
