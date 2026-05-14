const express = require('express')
const app = express()
app.get('/api/express_hello', (req, res) => { res.send('ok') })
app.listen(3000)
