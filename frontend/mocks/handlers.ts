import { http, HttpResponse } from 'msw';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export const handlers = [
  // Auth endpoints
  http.get(`${API_BASE_URL}/api/auth/me`, () => {
    return HttpResponse.json({
      id: 'test-user-id',
      discordId: 'test-discord-id',
      username: 'testuser',
      avatar: 'https://cdn.discordapp.com/avatars/test.png',
    });
  }),

  http.post(`${API_BASE_URL}/api/auth/logout`, () => {
    return HttpResponse.json({ success: true });
  }),

  // Feeds endpoints
  http.get(`${API_BASE_URL}/api/feeds`, () => {
    return HttpResponse.json([
      {
        id: 'feed-1',
        name: 'Tech Blog',
        url: 'https://example.com/feed',
        category: 'Technology',
        isSubscribed: false,
      },
      {
        id: 'feed-2',
        name: 'Science News',
        url: 'https://science.example.com/feed',
        category: 'Science',
        isSubscribed: true,
      },
    ]);
  }),

  http.post(`${API_BASE_URL}/api/subscriptions/toggle`, async ({ request }) => {
    const body = (await request.json()) as { feed_id: string };
    return HttpResponse.json({
      feedId: body.feed_id,
      isSubscribed: true,
    });
  }),

  // Articles endpoints
  http.get(`${API_BASE_URL}/api/articles/me`, ({ request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const pageSize = parseInt(url.searchParams.get('page_size') || '20');

    return HttpResponse.json({
      articles: [
        {
          id: 'article-1',
          title: 'Test Article 1',
          url: 'https://example.com/article-1',
          feedName: 'Tech Blog',
          category: 'Technology',
          publishedAt: new Date().toISOString(),
          tinkeringIndex: 4,
          aiSummary: 'This is a test article summary.',
        },
      ],
      page,
      pageSize,
      totalCount: 1,
      hasNextPage: false,
    });
  }),
];
