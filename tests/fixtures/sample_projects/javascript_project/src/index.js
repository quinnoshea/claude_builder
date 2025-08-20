const express = require('express');
const _ = require('lodash');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

app.get('/', (req, res) => {
    res.json({ message: 'Hello, World!', timestamp: new Date().toISOString() });
});

app.get('/api/data', (req, res) => {
    const data = _.range(1, 11).map(id => ({ id, value: `Item ${id}` }));
    res.json(data);
});

if (require.main === module) {
    app.listen(PORT, () => {
        console.log(`Server running on port ${PORT}`);
    });
}

module.exports = app;