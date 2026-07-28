const pool = require("../config/db");
const bcrypt = require("bcrypt");
const jwt = require("jsonwebtoken");

const login = async (req, res) => {
  try {

    const { username, password } = req.body;

    // Find user
    const result = await pool.query(
      `SELECT ua.*, r.role_name
       FROM user_account ua
       JOIN roles r ON ua.role_id = r.role_id
       WHERE ua.username = $1`,
      [username]
    );

    if (result.rows.length === 0) {
      return res.status(401).json({
        message: "Invalid username or password"
      });
    }

    const user = result.rows[0];

    // Compare password
    const isMatch = await bcrypt.compare(
      password,
      user.password_hash
    );

    if (!isMatch) {
      return res.status(401).json({
        message: "Invalid username or password"
      });
    }

    // Generate JWT
    const token = jwt.sign(
      {
        userId: user.user_id,
        role: user.role_name
      },
      process.env.JWT_SECRET,
      {
        expiresIn: "1d"
      }
    );

    res.status(200).json({
      message: "Login Successful",
      token,
      user: {
        id: user.user_id,
        username: user.username,
        role: user.role_name
      }
    });

  } catch (error) {

    console.error(error);

    res.status(500).json({
      message: "Server Error"
    });

  }
};

module.exports = {
  login
};