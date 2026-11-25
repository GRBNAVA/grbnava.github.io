
document.addEventListener("DOMContentLoaded", async () => {

  const catalogos = document.querySelectorAll(".catalogo[data-posts]");

  async function carregarPost(caminho) {
    try {
      const resposta = await fetch(caminho);

      if (!resposta.ok) {
        throw new Error("Não foi possível carregar: " + caminho);
      }

      return await resposta.text();

    } catch (erro) {
      console.error(erro);
      return "";
    }
  }

  for (const catalogo of catalogos) {

    const caminhos = catalogo.dataset.posts
      .split(",")
      .map(caminho => caminho.trim())
      .filter(Boolean);

    const posts = await Promise.all(
      caminhos.map(caminho => carregarPost(caminho))
    );

    catalogo.innerHTML = posts.join("\n");

  }

});
