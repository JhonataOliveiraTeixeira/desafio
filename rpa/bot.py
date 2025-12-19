import os
import re
import time
import traceback
import requests
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from webdriver_manager.chrome import ChromeDriverManager


# =========================================================
# CONFIGURAÇÃO SIMPLES (EDITÁVEL POR QUALQUER PESSOA)
# =========================================================
# Auto reexecução dentro do próprio código
AUTO_RUN_ENABLED = True

# "interval" = roda a cada X minutos
# "daily"    = roda em horários fixos (HH:MM)
SCHEDULE_MODE = "daily"  # "interval" ou "daily"

# Se SCHEDULE_MODE == "interval"
RUN_EVERY_MINUTES = 60

# Se SCHEDULE_MODE == "daily"
RUN_AT_TIMES = ["00:30"]  # ex: ["00:30", "12:30", "18:00"]

# Operação do robô
LOOKBACK_DAYS_DEFAULT = 3   # requisito: hoje + 3 datas anteriores
HEADLESS_DEFAULT = True     # True = não abre janela do Chrome
KEEP_BROWSER_OPEN_ON_DEBUG = False  # True = segura browser aberto no fim (debug)

# Timeouts
SELENIUM_WAIT_SECONDS = 25
HTTP_TIMEOUT_SECONDS = 15


# =========================================================
# CONFIG / ENV
# =========================================================
raiz_projeto = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=raiz_projeto / ".env")

BASE_URL = os.getenv("RPA_BASE_URL", "https://normas.receita.fazenda.gov.br/sijut2consulta/consulta.action")
API_URL = os.getenv("RPA_API_URL", "http://127.0.0.1:8000/atos/")
TOKEN_URL = os.getenv("RPA_TOKEN_URL", "http://127.0.0.1:8000/token")

# >>> NOVO: endpoint de logs (sua rota é POST /logs/)
LOGS_URL = os.getenv("RPA_LOGS_URL", "http://127.0.0.1:8000/logs/")

ADMIN_USER = os.getenv("ADMIN_USER", "admin").strip()
ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "adminpassword").strip()

AUTH_TOKEN: Optional[str] = None

Locator = Tuple[str, str]


# =========================================================
# AUTH
# =========================================================
def get_auth_token() -> bool:
    global AUTH_TOKEN
    try:
        print(f"[*] Autenticando na API como '{ADMIN_USER}'...")
        resp = requests.post(
            TOKEN_URL,
            data={"username": ADMIN_USER, "password": ADMIN_PASS},
            timeout=HTTP_TIMEOUT_SECONDS
        )

        if resp.status_code == 200:
            AUTH_TOKEN = resp.json().get("access_token")
            if not AUTH_TOKEN:
                print("[-] Token não veio no response.")
                return False
            print("[+] Token obtido com sucesso.")
            return True

        print(f"[-] Falha ao autenticar ({resp.status_code}): {resp.text}")
        return False
    except Exception as e:
        print(f"[-] Erro ao autenticar: {e}")
        return False


# =========================================================
# SELENIUM
# =========================================================
def setup_driver(headless: bool = False):
    service = ChromeService(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, SELENIUM_WAIT_SECONDS)
    return driver, wait


def click_safely(driver, element):
    try:
        element.click()
    except WebDriverException:
        driver.execute_script("arguments[0].click();", element)


def set_value_with_events(driver, element, value: str):
    driver.execute_script("""
        const el = arguments[0];
        const val = arguments[1];

        if (el.hasAttribute('readonly')) el.removeAttribute('readonly');

        el.focus();
        el.value = '';
        el.value = val;
        el.setAttribute('value', val);

        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        el.dispatchEvent(new Event('blur', { bubbles: true }));
    """, element, value)


def fill_date_input(driver, element, value: str):
    """
    Campo de data com máscara:
    - tenta digitar como humano
    - reforça via JS + eventos
    """
    try:
        element.click()
        element.send_keys(Keys.CONTROL, "a")
        element.send_keys(Keys.BACKSPACE)
        element.send_keys(value)
        time.sleep(0.12)
    except Exception:
        pass

    set_value_with_events(driver, element, value)


def find_clickable_any(driver, wait, locators: List[Locator]):
    last = None
    for by, value in locators:
        try:
            el = wait.until(EC.element_to_be_clickable((by, value)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            return el
        except Exception as e:
            last = e
    raise last if last else TimeoutException("Elemento não encontrado.")


def pick_date_inputs(driver):
    dt_ini = driver.find_elements(By.ID, "dt_inicio")
    dt_fim = driver.find_elements(By.ID, "dt_fim")
    if dt_ini and dt_fim and dt_ini[0].is_displayed() and dt_fim[0].is_displayed():
        return dt_ini[0], dt_fim[0]

    candidates = driver.find_elements(By.CSS_SELECTOR, "input.form-control.maskDate, input[maxlength='10']")
    visibles = [c for c in candidates if c.is_displayed() and c.is_enabled()]
    if len(visibles) >= 2:
        return visibles[0], visibles[1]

    raise TimeoutException("Não consegui identificar 2 campos de data visíveis.")


def ensure_radio_publicacao(driver, wait) -> bool:
    radio = wait.until(EC.presence_of_element_located((By.ID, "daPublicacao")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", radio)
    driver.execute_script("""
        const r = arguments[0];
        r.checked = true;
        r.dispatchEvent(new Event('change', { bubbles: true }));
        r.click();
    """, radio)
    time.sleep(0.15)
    return driver.execute_script("return document.getElementById('daPublicacao')?.checked === true;")


def ensure_checkbox_atos_vigentes_desmarcado(driver):
    # Garante que "Apenas atos vigentes" NÃO esteja marcado
    try:
        cbs = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
        for cb in cbs:
            try:
                if cb.is_displayed() and cb.is_enabled() and cb.is_selected():
                    click_safely(driver, cb)
            except Exception:
                continue
    except Exception:
        pass


def wait_results_or_empty(wait):
    return wait.until(
        EC.any_of(
            EC.presence_of_element_located((By.ID, "tabelaAtos")),
            EC.presence_of_element_located((By.XPATH, "//*[contains(normalize-space(.),'Nenhum ato')]")),
            EC.presence_of_element_located((By.XPATH, "//*[contains(normalize-space(.),'Nenhum ato publicado')]")),
        )
    )


def page_has_no_results(driver) -> bool:
    src = driver.page_source
    return ("Nenhum ato" in src) or ("Nenhum ato publicado" in src)


# =========================================================
# EXTRAÇÃO
# =========================================================
def parse_numero_ato(tipo_ato: str) -> int:
    m = re.search(r"(\d+)", tipo_ato or "")
    return int(m.group(1)) if m else 0


def build_header_index_map(table_el) -> Dict[str, int]:
    headers = []
    try:
        ths = table_el.find_elements(By.CSS_SELECTOR, "thead th")
        headers = [h.text.strip().lower() for h in ths]
    except Exception:
        headers = []

    if not headers:
        try:
            ths = table_el.find_elements(By.CSS_SELECTOR, "tr th")
            headers = [h.text.strip().lower() for h in ths]
        except Exception:
            headers = []

    idx = {}
    for i, h in enumerate(headers):
        idx[h] = i
    return idx


def pick_col(idx_map: Dict[str, int], candidates: List[str]) -> Optional[int]:
    for c in candidates:
        for k, i in idx_map.items():
            if c in k:
                return i
    return None


def extract_rows(driver, wait) -> List[Dict]:
    """
    Retorna dicts com:
    - tipo_ato
    - numero_ato
    - orgao
    - publicacao_texto
    - ementa
    """
    table = wait.until(EC.presence_of_element_located((By.ID, "tabelaAtos")))
    idx_map = build_header_index_map(table)

    col_tipo = pick_col(idx_map, ["tipo do ato", "tipo"])
    col_orgao = pick_col(idx_map, ["órgão", "orgao", "unidade"])
    col_pub = pick_col(idx_map, ["publicação", "publicacao"])
    col_ementa = pick_col(idx_map, ["ementa"])

    fallback = {"tipo": 0, "orgao": 2, "pub": 3, "ementa": 4}

    linhas = table.find_elements(By.CSS_SELECTOR, "tbody tr")
    results = []

    for tr in linhas:
        tds = tr.find_elements(By.TAG_NAME, "td")
        if len(tds) < 4:
            continue

        i_tipo = col_tipo if col_tipo is not None else fallback["tipo"]
        i_orgao = col_orgao if col_orgao is not None else fallback["orgao"]
        i_pub = col_pub if col_pub is not None else fallback["pub"]
        i_ementa = col_ementa if col_ementa is not None else fallback["ementa"]

        if max(i_tipo, i_orgao, i_pub, i_ementa) >= len(tds):
            continue

        tipo_ato = tds[i_tipo].text.strip()
        orgao = tds[i_orgao].text.strip()
        publicacao = tds[i_pub].text.strip()
        ementa = tds[i_ementa].text.strip()

        results.append({
            "tipo_ato": tipo_ato,
            "numero_ato": parse_numero_ato(tipo_ato),
            "orgao": orgao,
            "publicacao_texto": publicacao,
            "ementa": ementa,
        })

    return results


# =========================================================
# PAGINAÇÃO (opcional)
# =========================================================
def try_go_next_page(driver, wait) -> bool:
    """
    Se houver paginação, tenta avançar.
    Retorna True se avançou.
    """
    next_locators = [
        (By.XPATH, "//a[contains(.,'Próxima') or contains(.,'Proxima')]"),
        (By.CSS_SELECTOR, "a[title*='Próxima'], a[title*='Proxima']"),
        (By.CSS_SELECTOR, "li.next a"),
    ]

    for by, sel in next_locators:
        try:
            el = driver.find_element(by, sel)
            if not el.is_displayed():
                continue

            # se estiver desabilitado
            try:
                parent = el.find_element(By.XPATH, "./..")
                cls = (parent.get_attribute("class") or "").lower()
                if "disabled" in cls:
                    return False
            except Exception:
                pass

            click_safely(driver, el)
            wait.until(EC.presence_of_element_located((By.ID, "tabelaAtos")))
            time.sleep(0.25)
            return True
        except Exception:
            continue

    return False


# =========================================================
# API - ATOS
# =========================================================
def send_to_api(items: List[Dict], data_execucao_iso: str) -> Tuple[int, int]:
    if not AUTH_TOKEN:
        raise RuntimeError("AUTH_TOKEN não definido")

    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}

    ok = 0
    fail = 0

    for it in items:
        payload = {
            "tipo_ato": it["tipo_ato"],
            "numero_ato": it["numero_ato"],
            "orgao": it["orgao"],
            "ementa": it["ementa"],
            "data_publicacao": data_execucao_iso,  # data do filtro (dia consultado)
            "publicacao_texto": it.get("publicacao_texto", ""),
        }

        try:
            r = requests.post(API_URL, json=payload, headers=headers, timeout=HTTP_TIMEOUT_SECONDS)
            if r.status_code in (200, 201):
                ok += 1
            elif r.status_code == 409:
                ok += 1
            else:
                fail += 1
                print(f"      [ERRO] {r.status_code} ao enviar {it['tipo_ato']}: {r.text}")
        except Exception as e:
            fail += 1
            print(f"      [EXCEÇÃO] Falha ao enviar item: {e}")

    return ok, fail


# =========================================================
# API - LOGS  (NOVO)
# =========================================================
def send_execution_log(
    registros_capturados: int,
    tempo_execucao_segundos: float,
    status: str,
    mensagem_erro: Optional[str] = None
) -> bool:
    """
    Envia 1 log para a API /logs/
    Seu model (não alterado):
      data_hora (default), registros_capturados, tempo_execucao_segundos, status, mensagem_erro
    """
    if not AUTH_TOKEN:
        print("[-] Sem AUTH_TOKEN para enviar log.")
        return False

    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}

    payload = {
        "registros_capturados": int(registros_capturados),
        "tempo_execucao_segundos": float(tempo_execucao_segundos),
        "status": status,
        "mensagem_erro": mensagem_erro
    }

    try:
        r = requests.post(LOGS_URL, json=payload, headers=headers, timeout=HTTP_TIMEOUT_SECONDS)
        if r.status_code in (200, 201):
            print("[+] Log salvo em /logs/.")
            return True

        print(f"[-] Falha ao salvar log ({r.status_code}): {r.text}")
        return False
    except Exception as e:
        print(f"[-] Exceção ao salvar log: {e}")
        return False


# =========================================================
# RPA CORE  (ALTERADO PARA GERAR LOG)
# =========================================================
def run_rpa(lookback_days: int, headless: bool, keep_open: bool):
    started_at = datetime.now()
    error_messages: List[str] = []

    total_ok = 0
    total_fail = 0
    total_new = 0

    driver = None

    try:
        if not get_auth_token():
            error_messages.append("Falha ao autenticar na API (token).")
            print("[-] Abortando: não autenticou na API.")
            return

        driver, wait = setup_driver(headless=headless)

        # dedupe entre dias e páginas
        seen = set()

        for offset in range(0, lookback_days + 1):
            alvo = date.today() - timedelta(days=offset)
            data_str = alvo.strftime("%d/%m/%Y")
            data_iso = alvo.isoformat()

            print(f"\n[*] Buscando por 'da publicação' em: {data_str} (offset -{offset}d)")
            driver.get(BASE_URL)

            try:
                ensure_radio_publicacao(driver, wait)
                ensure_checkbox_atos_vigentes_desmarcado(driver)

                time.sleep(0.4)
                dt_ini, dt_fim = pick_date_inputs(driver)

                fill_date_input(driver, dt_ini, data_str)
                fill_date_input(driver, dt_fim, data_str)

                # Debug opcional
                print("    [DEBUG] dt_inicio.value =", dt_ini.get_attribute("value"))
                print("    [DEBUG] dt_fim.value    =", dt_fim.get_attribute("value"))

                btn_locators = [
                    (By.ID, "btnSubmit"),
                    (By.CSS_SELECTOR, "button#btnSubmit"),
                    (By.XPATH, "//button[contains(normalize-space(.),'Buscar')]"),
                ]
                btn_buscar = find_clickable_any(driver, wait, btn_locators)
                click_safely(driver, btn_buscar)

                wait_results_or_empty(wait)
                time.sleep(0.2)

                if page_has_no_results(driver):
                    print("    [!] Sem resultados nessa data.")
                    continue

                # Extrai (com paginação se existir)
                items_to_send: List[Dict] = []
                while True:
                    rows = extract_rows(driver, wait)

                    for r in rows:
                        key = (
                            r.get("tipo_ato", ""),
                            r.get("numero_ato", 0),
                            r.get("orgao", ""),
                            r.get("publicacao_texto", ""),
                            r.get("ementa", ""),
                        )
                        if key in seen:
                            continue
                        seen.add(key)
                        items_to_send.append(r)

                    if not try_go_next_page(driver, wait):
                        break

                print(f"    [+] Capturados (novos) na data {data_str}: {len(items_to_send)}")
                total_new += len(items_to_send)

                if items_to_send:
                    ok, fail = send_to_api(items_to_send, data_iso)
                    total_ok += ok
                    total_fail += fail
                    print(f"    [API] OK: {ok} | Falhas: {fail}")

            except Exception as e:
                msg = f"Erro ao processar {data_str}: {repr(e)}"
                error_messages.append(msg)
                print(f"    [ERRO] {msg}")
                traceback.print_exc()

        print("\n===== RESUMO =====")
        print(f"Total capturado (novo): {total_new}")
        print(f"Total enviado OK:       {total_ok}")
        print(f"Total falhas:           {total_fail}")

    finally:
        finished_at = datetime.now()
        tempo_execucao = (finished_at - started_at).total_seconds()

        # Define status do log
        if error_messages and total_ok == 0 and total_new == 0:
            status = "failed"
        elif total_fail > 0 or error_messages:
            status = "partial"
        else:
            status = "success"

        mensagem_erro = "\n".join(error_messages) if error_messages else None

        # Salva log no backend
        if AUTH_TOKEN:
            send_execution_log(
                registros_capturados=total_new,
                tempo_execucao_segundos=tempo_execucao,
                status=status,
                mensagem_erro=mensagem_erro
            )

        # Fecha o navegador
        try:
            if driver:
                if keep_open:
                    input("\n[PAUSA] Aperte ENTER para fechar o navegador...")
                driver.quit()
        except Exception:
            pass


# =========================================================
# SCHEDULER INTERNO (AUTO REEXECUÇÃO)
# =========================================================
def seconds_until_next_daily_run(times_hhmm: List[str]) -> int:
    now = datetime.now()
    candidates: List[datetime] = []
    for hhmm in times_hhmm:
        hh, mm = map(int, hhmm.split(":"))
        run_dt = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if run_dt <= now:
            run_dt += timedelta(days=1)
        candidates.append(run_dt)
    next_run = min(candidates)
    return max(1, int((next_run - now).total_seconds()))


def run_forever():
    print("\n[SCHEDULER] Auto-run habilitado.")
    print(f"[SCHEDULER] Modo: {SCHEDULE_MODE}")

    while True:
        started_at = datetime.now()
        print(f"\n[SCHEDULER] Execução iniciada em {started_at:%Y-%m-%d %H:%M:%S}")

        try:
            run_rpa(
                lookback_days=LOOKBACK_DAYS_DEFAULT,
                headless=HEADLESS_DEFAULT,
                keep_open=KEEP_BROWSER_OPEN_ON_DEBUG
            )
            print("[SCHEDULER] Execução finalizada.")
        except KeyboardInterrupt:
            print("\n[SCHEDULER] Interrompido pelo usuário. Encerrando.")
            break
        except Exception as e:
            print(f"[SCHEDULER] ERRO na execução: {e}")
            traceback.print_exc()

        if not AUTO_RUN_ENABLED:
            print("[SCHEDULER] Auto-run desabilitado. Encerrando.")
            break

        if SCHEDULE_MODE == "interval":
            sleep_seconds = max(60, RUN_EVERY_MINUTES * 60)
            next_run = datetime.now() + timedelta(seconds=sleep_seconds)
            print(f"[SCHEDULER] Próxima execução (intervalo): {next_run:%Y-%m-%d %H:%M:%S}")
        elif SCHEDULE_MODE == "daily":
            sleep_seconds = seconds_until_next_daily_run(RUN_AT_TIMES)
            next_run = datetime.now() + timedelta(seconds=sleep_seconds)
            print(f"[SCHEDULER] Próxima execução (diária): {next_run:%Y-%m-%d %H:%M:%S}")
        else:
            print("[SCHEDULER] SCHEDULE_MODE inválido. Use 'interval' ou 'daily'. Encerrando.")
            break

        time.sleep(sleep_seconds)


# =========================================================
# ENTRYPOINT
# =========================================================
if __name__ == "__main__":
    if AUTO_RUN_ENABLED:
        run_forever()
    else:
        run_rpa(
            lookback_days=LOOKBACK_DAYS_DEFAULT,
            headless=HEADLESS_DEFAULT,
            keep_open=KEEP_BROWSER_OPEN_ON_DEBUG
        )
