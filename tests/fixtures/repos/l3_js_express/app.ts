// @ts-nocheck
// Fixture file for RepoSense AST matching. Not intended for TS typechecking.
const express = require('express');
const app = express();
const router = express.Router();
app.get("/hello", (req, res) => { res.send("ok"); });
router.post('/submit', (req, res) => { res.status(201).json({}); });
Promise.all([fetch('/a'), fetch('/b')]).then(() => {});
