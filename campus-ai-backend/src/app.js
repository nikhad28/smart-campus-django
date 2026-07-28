const express = require("express");
const cors = require("cors");

require("./config/db");

const studentRoutes = require("./routes/studentRoutes");
const authRoutes = require("./routes/authRoutes");

const app = express();

app.use(cors());
app.use(express.json());
app.use("/api/auth", authRoutes);

app.use("/api/students", studentRoutes);

app.get("/", (req, res) => {
  res.send("Campus AI Backend Running 🚀");
});

module.exports = app;