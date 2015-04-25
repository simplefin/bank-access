var q = require('q');
var system = require('system');
var DATASTORE_URL = system.env.DATASTORE_URL;

var username, password;

console.log(DATASTORE_URL);

var casper = require('casper').create();
casper.start();

casper.page.viewportSize = {
    width: 800,
    height: 600
};

casper.open(DATASTORE_URL + '/username?prompt=Username%3F', function() {
    username = this.page.plainText;
})
casper.thenOpen(DATASTORE_URL + '/password?prompt=Password%3F', function() {
    password = this.page.plainText;
})
casper.thenOpen('https://www.capitalone.com', function() {
    this.capture('/tmp/images/1.png');
    this.click('#btnAccountType');
    this.click('label[for="rbCreditCards"]')
    this.sendKeys('input[name="us-credit-cards-uid"]', username);
    this.sendKeys('input[name="us-credit-cards-pw"]', password);
    this.capture('/tmp/images/2.png');
    this.click('#submit-card-us');
    this.capture('/tmp/images/3.png');
})
casper.waitForUrl(/accounts$/, function() {
    this.capture('/tmp/images/4.png');
}, function() {
    this.echo('timeout');
    this.capture('/tmp/images/5.png');
}, 5000);
// casper.thenOpen('https://servicing.capitalone.com/C1/Login.aspx', function() {
// })
// casper.withFrame('loginframe', function() {
//     this.fill('form', {
//         username: username,
//         user: username,
//         password: password
//     }, true);
//     this.echo('submitted?');
//     this.echo(this.getPageContent());
// })

// casper.thenOpen('')
// casper.thenOpen('https://login1.capitalone.com/loginweb/login/login.do', {
//     method: 'post',
//     data: {
//         username: username,
//         user: username,
//         password: password
//     }
// },
//     function() {
//         this.echo(this.getPageContent());
// });


casper.run();
