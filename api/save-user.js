const fs = require('fs');
const path = require('path');

export default async function handler(req, res) {
    // Only allow POST requests
    if (req.method !== 'POST') {
        return res.status(405).json({ message: 'Method Not Allowed' });
    }

    try {
        const { name, age, gender } = req.body;

        // Basic validation
        if (!name || !age || !gender) {
            return res.status(400).json({ message: 'Missing required fields: name, age, or gender.' });
        }

        const newUser = {
            id: Date.now().toString(),
            name,
            age,
            gender,
            timestamp: new Date().toISOString()
        };

        // Path to users.json (in the root directory relative to the api folder)
        const filePath = path.join(process.cwd(), 'users.json');

        // Read existing users
        let users = [];
        try {
            const fileData = fs.readFileSync(filePath, 'utf8');
            users = JSON.parse(fileData);
        } catch (readError) {
            // If file doesn't exist or is empty/invalid, start with empty array
            console.warn("Could not read users.json, starting fresh.", readError.message);
        }

        // Add new user
        users.push(newUser);

        // Write back to file
        fs.writeFileSync(filePath, JSON.stringify(users, null, 2), 'utf8');

        // Return success
        return res.status(200).json({ message: 'User saved successfully', user: newUser });

    } catch (error) {
        console.error('Error saving user:', error);
        return res.status(500).json({ message: 'Internal Server Error' });
    }
}
