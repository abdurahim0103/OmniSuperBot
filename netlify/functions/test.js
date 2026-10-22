exports.handler = async () => {
  return {
    statusCode: 200,
    body: JSON.stringify({ ok: true, msg: "Netlify functions working!" })
  };
};
