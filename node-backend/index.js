import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import http from 'http';
import { Server } from 'socket.io';
import mongoose from 'mongoose';
import authRoutes from './routes/authRoutes.js';
import alertRoutes from './routes/alertRoutes.js';
import userRoutes from './routes/userRoutes.js';
import connectDB from './db.js'; // Import connection function

dotenv.config();

const app = express();
const PORT = process.env.PORT || 4000;

// Create HTTP server
const server = http.createServer(app);

// Initialize Socket.io
const io = new Server(server, {
    cors: {
        origin: "*", // Allow all origins (adjust for production)
        methods: ["GET", "POST"]
    }
});

// Connect to MongoDB
connectDB();

// Middlewares
app.use(cors());
app.use(express.json());

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/alerts', alertRoutes);
app.use('/api/users', userRoutes);

// Real-Time Logic: MongoDB Change Stream
mongoose.connection.once('open', () => {
    console.log("MongoDB Connected. Setting up Change Stream...");

    const reportCollection = mongoose.connection.collection('reports');
    const changeStream = reportCollection.watch();

    changeStream.on('change', async (change) => {
        if (change.operationType === 'insert') {
            const newReport = change.fullDocument;
            console.log("New Alert Detected:", newReport.disaster_type);

            // Emit to all connected clients
            io.emit('new_event', newReport);

            // --- Smart Notification Logic ---
            if (newReport.severity === 'High') {
                try {
                    // In a real app, you would fetch users with role='admin' or subscribed users
                    // const recipients = await User.find({ role: 'admin' }).select('email');

                    const emailSubject = `🚨 HIGH ALERT: ${newReport.disaster_type} in ${newReport.location_text || 'Unknown Location'}`;
                    const emailBody = `A high severity ${newReport.disaster_type} has been reported at ${newReport.location_text}. \nTime: ${newReport.timestamp}. \nPlease take action immediately.`;

                    // For DEMO: Log to console instead of sending actual email
                    console.log("\n==================================================");
                    console.log("📧 [MOCK EMAIL SENT]");
                    console.log(`To: admin@test.com`);
                    console.log(`Subject: ${emailSubject}`);
                    console.log(`Body: ${emailBody}`);
                    console.log("==================================================\n");

                    /* 
                    // Actual Nodemailer Code (Uncomment to use)
                    // import nodemailer from 'nodemailer';
                    // const transporter = nodemailer.createTransport({ ... });
                    // await transporter.sendMail({
                    //     from: '"Disaster Alert System" <alert@system.com>',
                    //     to: "admin@test.com",
                    //     subject: emailSubject,
                    //     text: emailBody
                    // });
                    */

                } catch (error) {
                    console.error("Failed to send notification email:", error);
                }
            }
        }
    });
});

// Socket.io Connection Handler
io.on('connection', (socket) => {
    console.log('New client connected:', socket.id);

    socket.on('disconnect', () => {
        console.log('Client disconnected:', socket.id);
    });
});

// Start server (using server.listen instead of app.listen)
server.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});