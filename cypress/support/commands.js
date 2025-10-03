// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add('login', (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add('drag', { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add('dismiss', { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite('visit', (originalFn, url, options) => { ... })
// cypress/support/commands.js
Cypress.Commands.add('loginByFacebook', () => {
  const username = Cypress.env('FB_USERNAME');
  const password = Cypress.env('FB_PASSWORD');

  if (!username || !password) {
    throw new Error('FB_USERNAME or FB_PASSWORD not set in Cypress env');
  }

  cy.visit('https://facebook.com'); // baseUrl is facebook.com
    cy.get('#email', { timeout: 10000 }).clear().type(username);
    cy.get('#pass').clear().type(password, { log: false });
    cy.get('[name="login"]').click();

    // wait for successful login — adjust selector for reliability
    cy.url({ timeout: 20000 }).should('not.include', '/login');

});
