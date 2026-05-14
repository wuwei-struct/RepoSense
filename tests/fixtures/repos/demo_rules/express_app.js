const express = require("express");
const app = express();
app.get("/hello", (req, res) => res.send("ok"));
app.post("/pay", (req, res) => res.send("ok"));
