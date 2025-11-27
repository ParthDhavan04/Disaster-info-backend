import express from 'express';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import User from '../models/User.js'; // Import the Mongoose Model
import dotenv from 'dotenv';

dotenv.config();
const router = express.Router();

// Signup route
router.post('/signup', async (req, res) => {
    const { fullname, email, password, role } = req.body;

    if (!fullname || !email || !password) {
        return res.status(400).json({ message: "All fields are required" });
    }

    try {
        // Check if user already exists (Mongoose Syntax)
        const userExists = await User.findOne({ email });

        if (userExists) {
            return res.status(400).json({ message: "User already exists" });
        }

        // Hash password
        const salt = await bcrypt.genSalt(10);
        const hashedPassword = await bcrypt.hash(password, salt);

        // Create new user
        const user = await User.create({
            fullname,
            email,
            password: hashedPassword,
            role: role || 'user' // Default to 'user' if not provided
        });

        // Respond
        res.status(201).json({
            message: "User created",
            user: { id: user._id, fullname: user.fullname, email: user.email, role: user.role }
        });

    } catch (err) {
        console.error(err);
        res.status(500).json({ message: "Server error" });
    }
});

// Login route
router.post('/login', async (req, res) => {
    const { email, password } = req.body;

    if (!email || !password) {
        return res.status(400).json({ message: "Email and password required" });
    }

    try {
        // Find user (Mongoose Syntax)
        const user = await User.findOne({ email });

        if (!user) {
            return res.status(400).json({ message: "Invalid credentials" });
        }

        // Compare password
        const isMatch = await bcrypt.compare(password, user.password);
        if (!isMatch) {
            return res.status(400).json({ message: "Invalid credentials" });
        }

        // Generate JWT
        const token = jwt.sign(
            { id: user._id, email: user.email, role: user.role },
            process.env.JWT_SECRET,
            { expiresIn: "1h" }
        );

        res.json({
            message: "Login successful",
            token,
            user: { id: user._id, fullname: user.fullname, email: user.email, role: user.role }
        });

    } catch (err) {
        console.error(err);
        res.status(500).json({ message: "Server error" });
    }
});

// Seed Admin Route (Temporary for testing)
router.get('/seed-admin', async (req, res) => {
    try {
        const adminEmail = "admin@test.com";
        const adminExists = await User.findOne({ email: adminEmail });

        if (adminExists) {
            return res.status(400).json({ message: "Admin already exists" });
        }

        const salt = await bcrypt.genSalt(10);
        const hashedPassword = await bcrypt.hash("admin123", salt);

        const admin = await User.create({
            fullname: "System Admin",
            email: adminEmail,
            password: hashedPassword,
            role: "admin"
        });

        res.status(201).json({
            message: "Admin user created successfully",
            user: { id: admin._id, email: admin.email, role: admin.role }
        });

    } catch (err) {
        console.error(err);
        res.status(500).json({ message: "Server error creating admin" });
    }
});

export default router;
