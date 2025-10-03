const { defineConfig } = require('cypress');
require('dotenv').config(); // loads process.env from .env

module.exports = defineConfig({
  e2e: {
    baseUrl: 'https://www.facebook.com',
    setupNodeEvents(on, config) {
      // implement node event listeners here
      config.env.FB_USERNAME = process.env.FB_USERNAME;
      config.env.FB_PASSWORD = process.env.FB_PASSWORD;
      return config;
    },
  },
});
