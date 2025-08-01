import { setupServer } from 'msw/node';
import { rest } from 'msw';
import { handlers } from './handlers';

// Setup MSW server with our request handlers
export const server = setupServer(...handlers);

// Additional server configuration for testing
server.events.on('request:start', ({ request }) => {
  console.log('MSW intercepted:', request.method, request.url);
});

server.events.on('request:match', ({ request }) => {
  console.log('MSW matched:', request.method, request.url);
});

server.events.on('request:unhandled', ({ request }) => {
  console.warn('MSW unhandled:', request.method, request.url);
});