from django.shortcuts import render

def truss_detail_page(request, truss_id: int):
    # O template carrega os dados via JS a partir de /static/truss-data/<id>.json
    return render(request, "accounts/truss_detail.html", {"truss_id": truss_id})