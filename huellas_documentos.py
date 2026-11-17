import hashlib


def huella(texto):
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]


doc1 = "Politica de devoluciones: 30 dias desde la compra."
doc2 = "Politica de devoluciones: 30 dias desde la compra."
doc3 = "Politica de envios: 5 dias habiles a todo el pais."

print("doc1 huella:", huella(doc1), "longitud:", len(doc1))
print("doc2 huella:", huella(doc2), "longitud:", len(doc2))
print("doc3 huella:", huella(doc3), "longitud:", len(doc3))
print("doc1 == doc2 (mismo contenido):", huella(doc1) == huella(doc2))