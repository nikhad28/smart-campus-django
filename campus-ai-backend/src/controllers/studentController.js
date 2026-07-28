const pool = require("../config/db");

const getStudents = async (req, res) => {
  try {
    const result = await pool.query(
      "SELECT * FROM student ORDER BY student_id"
    );

    res.status(200).json(result.rows);
  } catch (error) {
    console.error(error);
    res.status(500).json({
      message: "Error fetching students",
    });
  }
};

const addStudent = async (req, res) => {
  try {
    const {
      roll_no,
      full_name,
      gender,
      dob,
      whatsapp_no,
      admission_year,
      department_id,
      semester_id,
      division_id,
      parent_id
    } = req.body;

    const query = `
      INSERT INTO student
      (
        roll_no,
        full_name,
        gender,
        dob,
        whatsapp_no,
        admission_year,
        department_id,
        semester_id,
        division_id,
        parent_id
      )
      VALUES
      ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
      RETURNING *;
    `;

    const values = [
      roll_no,
      full_name,
      gender,
      dob,
      whatsapp_no,
      admission_year,
      department_id,
      semester_id,
      division_id,
      parent_id
    ];

    const result = await pool.query(query, values);

    res.status(201).json({
      message: "Student added successfully",
      student: result.rows[0]
    });

  } catch (error) {
    console.error(error);
    res.status(500).json({
      message: "Error adding student"
    });
  }
};

const getStudentById = async (req, res) => {
  try {
    const { id } = req.params;

    const result = await pool.query(
      "SELECT * FROM student WHERE student_id = $1",
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        message: "Student not found"
      });
    }

    res.status(200).json(result.rows[0]);

  } catch (error) {
    console.error(error);
    res.status(500).json({
      message: "Error fetching student"
    });
  }
};

const updateStudent = async (req, res) => {
  try {
    const { id } = req.params;

    const {
      roll_no,
      full_name,
      gender,
      dob,
      whatsapp_no,
      admission_year,
      department_id,
      semester_id,
      division_id,
      parent_id
    } = req.body;

    const query = `
      UPDATE student
      SET
        roll_no = $1,
        full_name = $2,
        gender = $3,
        dob = $4,
        whatsapp_no = $5,
        admission_year = $6,
        department_id = $7,
        semester_id = $8,
        division_id = $9,
        parent_id = $10
      WHERE student_id = $11
      RETURNING *;
    `;

    const values = [
      roll_no,
      full_name,
      gender,
      dob,
      whatsapp_no,
      admission_year,
      department_id,
      semester_id,
      division_id,
      parent_id,
      id
    ];

    const result = await pool.query(query, values);

    if (result.rows.length === 0) {
      return res.status(404).json({
        message: "Student not found"
      });
    }

    res.status(200).json({
      message: "Student updated successfully",
      student: result.rows[0]
    });

  } catch (error) {
    console.error(error);
    res.status(500).json({
      message: "Error updating student"
    });
  }
};

const deleteStudent = async (req, res) => {
  try {
    const { id } = req.params;

    const result = await pool.query(
      "DELETE FROM student WHERE student_id = $1 RETURNING *",
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        message: "Student not found"
      });
    }

    res.status(200).json({
      message: "Student deleted successfully"
    });

  } catch (error) {
    console.error(error);
    res.status(500).json({
      message: "Error deleting student"
    });
  }
};

module.exports = {
  getStudents,
  getStudentById,
  addStudent,
  updateStudent,
  deleteStudent
};