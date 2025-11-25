import express from 'express';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import User from '../models/User.js'; // Import the Mongoose Model
import dotenv from 'dotenv';

dotenv.config();
const router = express.Router();

// Signup route
router.post('/signup', async (req, res) => {
    const { fullname, email, password } = req.body;

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
            password: hashedPassword
        });

        // Respond
        res.status(201).json({ 
            message: "User created", 
            user: { id: user._id, fullname: user.fullname, email: user.email } 
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
        const token = jwt.sign({ id: user._id, email: user.email }, process.env.JWT_SECRET, { expiresIn: "1h" });

        res.json({ 
            message: "Login successful", 
            token, 
            user: { id: user._id, fullname: user.fullname, email: user.email } 
        });

    } catch (err) {
        console.error(err);
        res.status(500).json({ message: "Server error" });
    }
});

export default router;