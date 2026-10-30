import sys
import os
import pickle
import urllib.request
import bs4
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

URLS = [
    "https://www.ghana.accessbankplc.com",
    "https://www.ghana.accessbankplc.com/personal",
    "https://www.ghana.accessbankplc.com/personal/loans",
    "https://www.ghana.accessbankplc.com/personal/loans/personal-loan",
    "https://www.ghana.accessbankplc.com/personal/loans/payday-loan",
    "https://www.ghana.accessbankplc.com/personal/loans/cash-backed-loan",
    "https://www.ghana.accessbankplc.com/personal/loans/vehicle-finance",
    "https://www.ghana.accessbankplc.com/personal/loans/device-finance",
    "https://www.ghana.accessbankplc.com/personal/loans/w-power-loan",
    "https://www.ghana.accessbankplc.com/personal/savings-investing",
    "https://www.ghana.accessbankplc.com/personal/savings-investing/access-savings-account",
    "https://www.ghana.accessbankplc.com/personal/money-transfer",
    "https://www.ghana.accessbankplc.com/personal/money-transfer/western-union",
    "https://www.ghana.accessbankplc.com/personal/money-transfer/moneygram",
    "https://www.ghana.accessbankplc.com/personal/segments/youth",
    "https://www.ghana.accessbankplc.com/personal/insure/bancassurance",
    "https://www.ghana.accessbankplc.com/business",
    "https://www.ghana.accessbankplc.com/business/emerging-businesses",
    "https://www.ghana.accessbankplc.com/business/emerging-businesses/loans",
    "https://www.ghana.accessbankplc.com/business/emerging-businesses/sme-zone",
    "https://www.ghana.accessbankplc.com/business/trade-finance/letter-of-credit",
    "https://www.ghana.accessbankplc.com/corporate",
    "https://www.ghana.accessbankplc.com/corporate/products-services",
    "https://www.ghana.accessbankplc.com/corporate/products-services/financing",
    "https://www.ghana.accessbankplc.com/corporate/products-services/cash-management",
    "https://www.ghana.accessbankplc.com/ways-to-bank",
    "https://www.ghana.accessbankplc.com/ways-to-bank/access-mobile-app",
    "https://www.ghana.accessbankplc.com/ways-to-bank/cards",
    "https://www.ghana.accessbankplc.com/ways-to-bank/atm",
    "https://www.ghana.accessbankplc.com/ways-to-bank/901",
    "https://www.ghana.accessbankplc.com/contact-us",
    "https://www.ghana.accessbankplc.com/contact-us/branch-atm-locator",
    "https://www.ghana.accessbankplc.com/about-us",
    "https://www.ghana.accessbankplc.com/about-us/corporate-profile",
    "https://www.ghana.accessbankplc.com/about-us/our-history",
    "https://www.ghana.accessbankplc.com/help",
    "https://www.ghana.accessbankplc.com/help/online-security-tips",
    "https://www.ghana.accessbankplc.com/private/hni/affluent",
    "https://www.ghana.accessbankplc.com/private/hni/summit",
]

CACHE_FILE = os.path.join(os.path.dirname(__file__), "website_cache.pkl")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def fetch_page_content(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    
    soup = bs4.BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "noscript", "svg"]):
        tag.decompose()
    
    text = " ".join(soup.stripped_strings)
    title = soup.title.get_text(strip=True) if soup.title else url
    return Document(page_content=text, metadata={"source": url, "title": title})


KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "knowledge")

def load_local_knowledge():
    local_docs = []
    if os.path.exists(KNOWLEDGE_DIR):
        for filename in os.listdir(KNOWLEDGE_DIR):
            filepath = os.path.join(KNOWLEDGE_DIR, filename)
            if not os.path.isfile(filepath):
                continue
            
            # Plain Text / Markdown / JSON / CSV
            if filename.endswith((".txt", ".md", ".json", ".csv")):
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    if content.strip():
                        local_docs.append(Document(
                            page_content=content,
                            metadata={"source": f"Local Knowledge: {filename}", "title": filename}
                        ))
                        print(f"  📁 Loaded text document: {filename} ({len(content)} chars)")
                except Exception as e:
                    print(f"  ❌ Failed to load {filename}: {e}")

            # PDF Files (Brochures, Product Guides, Tariff Sheets)
            elif filename.endswith(".pdf"):
                try:
                    import pypdf
                    reader = pypdf.PdfReader(filepath)
                    text = ""
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    if text.strip():
                        local_docs.append(Document(
                            page_content=text,
                            metadata={"source": f"PDF Document: {filename}", "title": filename}
                        ))
                        print(f"  📄 Loaded PDF document: {filename} ({len(reader.pages)} pages, {len(text)} chars)")
                except Exception as e:
                    print(f"  ❌ Failed to load PDF {filename}: {e}")

    return local_docs


def load_website_data(force_refresh=False):
    local_docs = load_local_knowledge()

    if not force_refresh and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "rb") as f:
                cached_splits = pickle.load(f)
            if len(cached_splits) > 0:
                print(f"⚡ Loaded {len(cached_splits)} cached chunks instantly!")
                # Split any newly added local docs
                if local_docs:
                    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                    local_splits = splitter.split_documents(local_docs)
                    return cached_splits + local_splits
                return cached_splits
        except Exception as e:
            print(f"⚠️ Cache read error ({e}), re-scraping...")

    print(f"🌐 Scraping {len(URLS)} pages from Access Bank Ghana website...")
    all_docs = []

    for i, url in enumerate(URLS):
        try:
            doc = fetch_page_content(url)
            if len(doc.page_content.strip()) > 50:
                all_docs.append(doc)
                print(f"  ✅ [{i+1}/{len(URLS)}] {url} ({len(doc.page_content)} chars)")
            else:
                print(f"  ⚠️ [{i+1}/{len(URLS)}] Empty page: {url}")
        except Exception as e:
            print(f"  ❌ [{i+1}/{len(URLS)}] Failed: {url} — {e}")

    print(f"\n📄 Total pages successfully loaded: {len(all_docs)}")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    splits = text_splitter.split_documents(all_docs)

    if len(splits) > 0:
        try:
            with open(CACHE_FILE, "wb") as f:
                pickle.dump(splits, f)
            print(f"💾 Saved {len(splits)} chunks to cache ({CACHE_FILE}).")
        except Exception as e:
            print(f"⚠️ Could not save cache: {e}")

    if local_docs:
        local_splits = text_splitter.split_documents(local_docs)
        splits = splits + local_splits

    print(f"✂️ Total chunks created (web + local): {len(splits)}")
    return splits

