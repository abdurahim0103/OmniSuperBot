exports.handler = async (event) => {
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
    };

    if (event.httpMethod === 'OPTIONS') {
        return { statusCode: 200, headers, body: '' };
    }

    const url = event.queryStringParameters?.url;
    let filename = event.queryStringParameters?.filename || 'OmniSuper_Media.mp4';
    filename = filename.replace(/[^\w\.\-_]/g, '_');

    if (!url) {
        return {
            statusCode: 400,
            headers: { ...headers, 'Content-Type': 'application/json' },
            body: JSON.stringify({ error: 'URL parameter is required' })
        };
    }

    try {
        const response = await fetch(url, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Referer': 'https://www.tiktok.com/'
            }
        });

        if (!response.ok) {
            return {
                statusCode: response.status,
                headers: { ...headers, 'Content-Type': 'application/json' },
                body: JSON.stringify({ error: `Remote returned HTTP ${response.status}` })
            };
        }

        const contentType = response.headers.get('content-type') || 'application/octet-stream';
        const arrayBuffer = await response.arrayBuffer();
        const base64Data = Buffer.from(arrayBuffer).toString('base64');

        return {
            statusCode: 200,
            headers: {
                ...headers,
                'Content-Type': contentType,
                'Content-Disposition': `attachment; filename="${filename}"`,
                'Content-Length': String(arrayBuffer.byteLength),
                'Cache-Control': 'public, max-age=86400'
            },
            body: base64Data,
            isBase64Encoded: true
        };
    } catch (err) {
        return {
            statusCode: 500,
            headers: { ...headers, 'Content-Type': 'application/json' },
            body: JSON.stringify({ error: err.message })
        };
    }
};
