describe('Facebook smoke', () => {
  beforeEach(() => {
    cy.loginByFacebook();
  });

  it('loads the homepage and shows profile menu', () => {
    cy.visit('/');
    // example assertion — adjust to what reliably appears for your test account
    cy.get('header').should('exist');
    // or check an element only visible to logged-in users
    // cy.get('[aria-label="Create"]').should('exist');
  });
});
