const express = require("express");
const router = express.Router();

const authenticateToken = require("../middleware/authMiddleware");

const {
    getStudents,
    getStudentById,
    addStudent,
    updateStudent,
    deleteStudent
} = require("../controllers/studentController");

router.get("/", authenticateToken, getStudents);

router.get("/:id", authenticateToken, getStudentById);

router.post("/", authenticateToken, addStudent);

router.put("/:id", authenticateToken, updateStudent);

router.delete("/:id", authenticateToken, deleteStudent);

module.exports = router;