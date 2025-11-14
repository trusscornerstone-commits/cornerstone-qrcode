from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from .models import QrCodeTruss as Truss
import re
import pytz, re, os, shutil, time
import logging
from django.shortcuts import redirect

User = get_user_model()
logger = logging.getLogger("production_logger")
BOSTON_TZ = pytz.timezone("America/New_York")


def login_page(request):
    if request.method == "POST":
        identifier = request.POST.get("username") or request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=identifier, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get("next")
            if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
                return redirect(next_url)
            return redirect("home")
        messages.error(request, "Wrong user or password")
    return render(request, "accounts/login_page.html")


@login_required
def home(request):
    return render(request, "accounts/home.html")


@login_required
def truss_detail_view(request, pk: int):
    truss = get_object_or_404(Truss, pk=pk)
    return render(request, "accounts/truss_detail.html", {"truss": truss})


def truss_detail(request, truss_id: int):
    return truss_detail_view(request, pk=truss_id)


@login_required
def scan_truss_view(request):
    return render(request, "accounts/scan_truss.html")


@login_required
def truss_qr_view(request):
    qr_data = request.GET.get("qr", "").strip()
    if not qr_data:
        return render(request, "accounts/truss_detail.html", {"error": "Invalid QRCode"})

    # Exemplo: T03 QTY: 1 OF 2 45-02-14 NEW_LABEL BATCH: 250018A
    parts = qr_data.split()

    try:
        truss_id = parts[0]
        unit_number = int(parts[2])
        quantity = int(parts[4])
        span = parts[5]
        project = parts[6]
        floor = parts[-1].replace("BATCH:", "")
    except Exception:
        return render(request, "accounts/truss_detail.html", {"error": "Invalid QR Code format"})

    truss, _ = Truss.objects.get_or_create(
        truss_id=truss_id,
        unit_number=unit_number,
        floor=floor,
        defaults={
            "quantity": quantity,
            "span": span,
            "project": project,
        },
    )

    if request.method == "POST":
        truss.check_produced(request.user)
        handle_pdf_backup(truss.truss_id)
        #now_boston = timezone.now().astimezone(BOSTON_TZ).strftime("%m-%d-%Y %H:%M:%S")
        now = timezone.now()
        logger.info(
            f"User '{request.user.username}' marcou {truss.truss_id} (floor {floor}) "
            f"como produzido (Qty {unit_number}/{quantity}) às {now}"
        )
        return redirect(request.path + f"?qr={qr_data}")

    return render(request, "accounts/truss_detail.html", {"truss": truss})

def handle_pdf_backup(truss_id):
    """
    Move o PDF correspondente à truss para a pasta de backup.
    Se o arquivo estiver em uso, cria uma cópia.
    """
    base_path = r"C:\Users\FATEX\Documents\qrcodes"
    backup_path = os.path.join(base_path, "backup")

    if not os.path.exists(backup_path):
        os.makedirs(backup_path)

    pdf_name = f"({truss_id}) Truss Tags.Pdf"
    src = os.path.join(base_path, pdf_name)
    dst = os.path.join(backup_path, pdf_name)

    if not os.path.exists(src):
        return

    try:
        # Tenta mover normalmente
        shutil.move(src, dst)
        print(f"✅ PDF movido para backup: {dst}")
    except PermissionError:
        # Se estiver aberto, cria cópia
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_copy = os.path.join(backup_path, f"{truss_id}_copy_{timestamp}.pdf")
        shutil.copy2(src, backup_copy)
        print(f"⚠️ PDF em uso. Cópia criada: {backup_copy}")
    except Exception as e:
        print(f"⚠️ Erro ao mover PDF para backup: {e}")


@login_required
def em_construcao_view(request):
    return render(request, "accounts/em_construcao.html")


@staff_member_required
def list_users(request):
    users = list(User.objects.values("username", "email"))
    return JsonResponse({"users": users})


def logout_view(request):
    logout(request)
    return redirect("login")


def health(request):
    return JsonResponse({"status": "ok"})


def root_redirect(request):
    if request.user.is_authenticated:
        return redirect("home")
    return redirect("login")
