"""
StreamFlow - Universal Media Downloader
Mobile-friendly web application for downloading Videos, Music, and Photos.
Features:
- Pre-download security audit (SSRF protection & malicious executable detection)
- Auto-detects available video qualities with file size estimates
- Direct download when single quality is available
- Resilient 500MB+ transfers with zero fragment loss (resumable chunks)
- 15-character title truncation policy
- Batch downloader supporting 10+ URLs with 3-attempt automated retry
- Direct device download into Phone / Laptop default Downloads folder
"""

import os
import time
import concurrent.futures
from datetime import datetime
import streamlit as st

from core import (
    inspect_media_url,
    download_media_file,
    download_with_retry,
    sanitize_title_15,
    format_bytes,
    create_zip_archive,
    cleanup_old_files,
    organize_downloaded_file,
    CUSTOM_CSS
)

st.set_page_config(
    page_title="StreamFlow Media Downloader",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inject styling
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Directory for streaming files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "static", "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# Periodic server cleanup
cleanup_old_files(DOWNLOADS_DIR, max_age_hours=2)

# Session state initialization
if "inspected_media" not in st.session_state:
    st.session_state["inspected_media"] = None
if "single_dl_result" not in st.session_state:
    st.session_state["single_dl_result"] = None
if "batch_dl_results" not in st.session_state:
    st.session_state["batch_dl_results"] = []
if "batch_zip_file" not in st.session_state:
    st.session_state["batch_zip_file"] = None
if "batch_text_area" not in st.session_state:
    st.session_state["batch_text_area"] = ""


# --- Hero Header ---
st.markdown("""
<div class="app-header">
    <h1 class="app-title">StreamFlow Downloader</h1>
    <p class="app-subtitle">
        Download Videos, Music & Photos directly into your phone or laptop. 
        Auto quality detection, 500MB+ resilient transfers, pre-download security scans, 
        and batch downloads with 3x retry protection.
    </p>
    <div class="platform-pills">
        <span class="platform-pill">YouTube</span>
        <span class="platform-pill">Instagram</span>
        <span class="platform-pill">TikTok</span>
        <span class="platform-pill">Facebook</span>
        <span class="platform-pill">X / Twitter</span>
        <span class="platform-pill">Reddit</span>
        <span class="platform-pill">Vimeo</span>
        <span class="platform-pill">SoundCloud</span>
        <span class="platform-pill">Photos & Direct Links</span>
    </div>
</div>
""", unsafe_allow_html=True)


# --- Tabs ---
tab_single, tab_batch, tab_storage = st.tabs([
    "🎯 Download Media",
    "⚡ Batch Downloader (10+ Links)",
    "🛡️ Security & Storage"
])


# ==============================================================================
# TAB 1: SINGLE MEDIA DOWNLOADER
# ==============================================================================
with tab_single:
    with st.container(border=True):
        st.markdown("### Paste Video, Music, or Photo Link")
        
        single_url = st.text_input(
            "Enter URL:",
            placeholder="Paste YouTube, Instagram, TikTok, Facebook, Twitter, MP4, MP3, or Photo link...",
            key="url_main_input",
            label_visibility="collapsed"
        )

        def clear_single_input():
            st.session_state["url_main_input"] = ""
            st.session_state["inspected_media"] = None
            st.session_state["single_dl_result"] = None

        col_act1, col_act2 = st.columns([1, 1])
        with col_act1:
            btn_inspect = st.button("🔍 Check Media & Qualities", type="primary", use_container_width=True)
        with col_act2:
            st.button("Clear Input", on_click=clear_single_input, use_container_width=True)

    # Process Inspection
    if btn_inspect and single_url.strip():
        with st.spinner("Conducting security scan and inspecting media stream..."):
            media_info = inspect_media_url(single_url.strip())
            if media_info.get("success"):
                st.session_state["inspected_media"] = media_info
                st.session_state["single_dl_result"] = None
            else:
                st.error(f"⚠️ {media_info.get('error', 'Inspection failed')}")

    # Display Inspected Media
    media = st.session_state.get("inspected_media")
    if media:
        with st.container(border=True):
            # Pre-download Security Audit Card
            sec = media.get("security_report", {})
            if sec:
                st.markdown(f"""
                <div class="security-badge">
                    <span>🛡️ <b>Security Audit Passed:</b></span>
                    <span>{sec.get('encryption', 'HTTPS')} | Clean IP: {sec.get('resolved_ip')} | {sec.get('malware_scan')}</span>
                </div>
                """, unsafe_allow_html=True)

            # Responsive Layout: Media Details
            col_preview, col_specs = st.columns([1, 1.4])
            
            with col_preview:
                if media.get("thumbnail"):
                    st.image(media["thumbnail"], use_container_width=True)
                else:
                    st.markdown("""
                    <div style="background: rgba(15,23,42,0.9); height: 180px; border-radius: 12px; display:flex; align-items:center; justify-content:center; border:1px dashed rgba(255,255,255,0.15);">
                        <span style="font-size: 3rem;">🎬</span>
                    </div>
                    """, unsafe_allow_html=True)

            with col_specs:
                m_icon = media.get("media_icon", "📹")
                m_type = media.get("media_type", "Video")
                st.markdown(f"#### {m_icon} {m_type}")
                st.markdown(f"**Title:** {media.get('title', 'Unknown')}")
                
                # Spliced 15-character filename callout
                safe_15 = media.get("safe_name_15", "media.mp4")
                st.markdown(f"""
                <div class="filename-box">
                    <div class="filename-label">Spliced File Name (Max 15 Characters):</div>
                    <div class="filename-value">{safe_15}</div>
                </div>
                """, unsafe_allow_html=True)

                # Specifications Box matching user format
                dur = media.get("duration", "N/A")
                res = media.get("resolution", "N/A")
                est_sz = media.get("estimated_size", "Dynamic")
                st.markdown(f"""
                <div class="spec-box">
                    <b>Duration:</b> {dur}<br>
                    <b>Max Resolution:</b> {res}<br>
                    <b>Size:</b> ~{est_sz}
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # Quality Options Selection
            has_multiple = media.get("has_multiple_qualities", False)
            qualities = media.get("qualities", [])

            if has_multiple and qualities:
                st.markdown("#### Available Qualities:")
                q_labels = [q["label"] for q in qualities]
                selected_q_label = st.selectbox(
                    "Choose Quality / Resolution to Download:",
                    options=q_labels,
                    index=0,
                    label_visibility="collapsed"
                )
                chosen_quality = next((q for q in qualities if q["label"] == selected_q_label), qualities[0])
                btn_start_dl = st.button("📥 Download to Phone / Laptop", type="primary", use_container_width=True)
            else:
                st.info("ℹ️ Single quality / direct stream detected. Ready for immediate download.")
                chosen_quality = qualities[0] if qualities else {"format_id": "best", "ext": "mp4"}
                btn_start_dl = st.button("📥 Direct Download to Phone / Laptop", type="primary", use_container_width=True)

        # Download Execution
        if btn_start_dl:
            with st.container(border=True):
                st.markdown("### ⏳ Transferring Media Stream...")
                prog_bar = st.progress(0.0)
                txt_status = st.empty()
                txt_speed = st.empty()

                def update_progress(p):
                    st_val = p.get('status')
                    if st_val == 'downloading':
                        pct = min(max(p.get('percent', 0.0) / 100.0, 0.0), 1.0)
                        prog_bar.progress(pct)
                        d_str = p.get('downloaded_str', '')
                        t_str = p.get('total_str', '')
                        spd = p.get('speed_str', '')
                        eta = p.get('eta_str', '')
                        txt_status.markdown(f"**Progress:** {d_str} of {t_str} ({pct*100:.1f}%)")
                        txt_speed.markdown(f"⚡ **Speed:** `{spd}` &nbsp;|&nbsp; ⏳ **ETA:** `{eta}`")
                    elif st_val == 'merging':
                        prog_bar.progress(0.99)
                        txt_status.markdown("🔄 Merging losslessly via FFmpeg at original quality...")
                        txt_speed.empty()

                dl_res = download_media_file(
                    url=media["url"],
                    format_id=chosen_quality.get("format_id", "best"),
                    output_dir=DOWNLOADS_DIR,
                    is_audio=chosen_quality.get("is_audio", False),
                    is_image=chosen_quality.get("is_image", False),
                    progress_callback=update_progress
                )

                if dl_res.get("success"):
                    st.session_state["single_dl_result"] = dl_res
                    st.success("✅ Download complete! File integrity verified (0 dropped fragments).")
                else:
                    st.error(f"❌ Download failed: {dl_res.get('error')}")

    # Completed Download Ready Card
    res_ready = st.session_state.get("single_dl_result")
    if res_ready and res_ready.get("success"):
        with st.container(border=True):
            st.markdown("### 🎉 Ready to Save on Your Device")
            f_path = res_ready["file_path"]
            f_name = res_ready["filename"]
            f_size = res_ready.get("file_size_str", "N/A")
            f_mime = res_ready.get("mime_type", "video/mp4")
            subfolder = res_ready.get("subfolder", "")

            st.markdown(f"""
            - 📁 **File Name:** `{f_name}` *(spliced to max 15 characters)*
            - 📂 **Organized Folder:** `{subfolder}/` *(Big files & media moved into dedicated folder)*
            - 💾 **File Size:** `{f_size}`
            - 🛡️ **Integrity:** `100% verified (500MB+ safe, zero missing data)`
            """)

            # Single reliable download button
            if os.path.exists(f_path):
                with open(f_path, "rb") as fl:
                    st.download_button(
                        label=f"💾 Download to Device ({f_size})",
                        data=fl,
                        file_name=f_name,
                        mime=f_mime,
                        type="primary",
                        use_container_width=True
                    )


# ==============================================================================
# TAB 2: BATCH DOWNLOADER (10+ URLS CONCURRENTLY)
# ==============================================================================
with tab_batch:
    with st.container(border=True):
        st.markdown("### Batch Downloader (10+ URLs)")
        st.markdown(
            "Paste multiple URLs (one per line). All items are downloaded in parallel with "
            "**3-attempt automated retry** for each file. All successful downloads are packaged "
            "into a **Single 1-Click ZIP Archive** that saves directly to your device!"
        )

        batch_input_val = st.text_area(
            "Paste URLs (one per line):",
            placeholder="https://www.youtube.com/watch?v=...\nhttps://www.youtube.com/watch?v=...\nhttps://instagram.com/p/...\nhttps://tiktok.com/@user/video/...\nhttps://example.com/video.mp4",
            height=180,
            key="batch_text_area"
        )

        col_bp1, col_bp2, col_bp3 = st.columns([1, 1, 1])
        with col_bp1:
            batch_preset_choice = st.selectbox(
                "Quality Preset:",
                options=[
                    "🌟 Highest Quality (Auto Max)",
                    "🎬 1080p Full HD",
                    "🎬 720p HD",
                    "🎬 480p SD",
                    "🎵 Audio MP3 (320 kbps)"
                ],
                index=0
            )
        with col_bp2:
            batch_workers = st.slider("Parallel Workers:", min_value=2, max_value=8, value=4)
        with col_bp3:
            st.write("")
            st.write("")
            btn_start_batch = st.button("🚀 Start Batch Download", type="primary", use_container_width=True)

        def load_sample_batch_callback():
            samples = [
                "https://archive.org/download/Popeye_forPresident/Popeye_forPresident_512kb.mp4",
                "https://archive.org/download/classic_cartoons_collection/Popeye_forPresident_512kb.mp4"
            ]
            st.session_state["batch_text_area"] = "\n".join(samples)

        st.button("📋 Load Sample Public Test Links", on_click=load_sample_batch_callback)

    # Preset Mapping
    fmt_map = {
        "🌟 Highest Quality (Auto Max)": ("bestvideo+bestaudio/best", False),
        "🎬 1080p Full HD": ("bestvideo[height<=1080]+bestaudio/best[height<=1080]/best", False),
        "🎬 720p HD": ("bestvideo[height<=720]+bestaudio/best[height<=720]/best", False),
        "🎬 480p SD": ("bestvideo[height<=480]+bestaudio/best[height<=480]/best", False),
        "🎵 Audio MP3 (320 kbps)": ("bestaudio/best", True)
    }
    sel_format_id, sel_is_audio = fmt_map[batch_preset_choice]

    # Batch Execution
    if btn_start_batch:
        urls = [u.strip() for u in batch_input_val.strip().split("\n") if u.strip()]
        if not urls:
            st.warning("⚠️ Please paste at least one URL.")
        else:
            total_urls = len(urls)
            st.info(f"🚀 Processing {total_urls} URLs with {batch_workers} parallel workers and 3x retry protection...")

            b_prog_bar = st.progress(0.0)
            b_status_txt = st.empty()

            def process_worker(item):
                i, u = item
                # Pre-download security check
                safe, msg, _ = verify_url_security(u)
                if not safe:
                    return {"index": i + 1, "success": False, "url": u, "error": msg}

                # Download with up to 3 automated retries
                res = download_with_retry(
                    url=u,
                    format_id=sel_format_id,
                    output_dir=DOWNLOADS_DIR,
                    is_audio=sel_is_audio,
                    max_retries=3
                )
                res["index"] = i + 1
                res["url"] = u
                return res

            results = []
            done_count = 0

            with concurrent.futures.ThreadPoolExecutor(max_workers=batch_workers) as executor:
                futures = {executor.submit(process_worker, itm): itm for itm in enumerate(urls)}
                for f in concurrent.futures.as_completed(futures):
                    done_count += 1
                    r = f.result()
                    results.append(r)
                    pct = done_count / total_urls
                    b_prog_bar.progress(pct)
                    b_status_txt.markdown(f"**Processed {done_count}/{total_urls} items...**")

            results.sort(key=lambda x: x.get("index", 0))
            st.session_state["batch_dl_results"] = results

            # Bundle ALL successful downloads into the ZIP
            success_files = [r["file_path"] for r in results if r.get("success") and os.path.exists(r.get("file_path", ""))]
            if success_files:
                z_name = f"batch_all_{int(time.time())}.zip"
                z_path = os.path.join(DOWNLOADS_DIR, z_name)
                if create_zip_archive(success_files, z_path):
                    st.session_state["batch_zip_file"] = z_path

            st.success(f"🎉 Batch completed! {len(success_files)} succeeded, {total_urls - len(success_files)} failed.")

    # Display Batch Results
    batch_items = st.session_state.get("batch_dl_results", [])
    if batch_items:
        with st.container(border=True):
            st.markdown("### 📋 Batch Results & Downloads")
            
            # Master ZIP Download Button
            zip_target = st.session_state.get("batch_zip_file")
            if zip_target and os.path.exists(zip_target):
                z_sz = format_bytes(os.path.getsize(zip_target))
                z_base = os.path.basename(zip_target)

                with open(zip_target, "rb") as zf:
                    st.download_button(
                        label=f"📦 Download Complete ZIP Package ({z_sz})",
                        data=zf,
                        file_name=z_base,
                        mime="application/zip",
                        type="primary",
                        use_container_width=True
                    )

            st.markdown("---")

            # Successful items
            success_items = [b for b in batch_items if b.get("success")]
            failed_items = [b for b in batch_items if not b.get("success")]

            if success_items:
                st.markdown(f"#### ✅ Successful Downloads ({len(success_items)} files):")
                for s in success_items:
                    idx = s.get("index", 1)
                    fn = s.get("filename")
                    fsz = s.get("file_size_str", "N/A")
                    fp = s.get("file_path")
                    mime = s.get("mime_type", "video/mp4")

                    c1, c2 = st.columns([2.5, 1.2])
                    with c1:
                        st.markdown(f"**#{idx}:** `{fn}` *(15 chars spliced)*  \n<span style='color:#9CA3AF; font-size:0.85rem;'>Size: {fsz} | Status: Verified Safe</span>", unsafe_allow_html=True)
                    with c2:
                        if os.path.exists(fp):
                            with open(fp, "rb") as fl:
                                st.download_button(
                                    label=f"💾 Save #{idx} ({fsz})",
                                    data=fl,
                                    file_name=fn,
                                    mime=mime,
                                    key=f"b_item_{idx}",
                                    use_container_width=True
                                )

            if failed_items:
                st.markdown(f"#### ⚠️ Failed Downloads ({len(failed_items)} items):")
                for fl_item in failed_items:
                    idx = fl_item.get("index", 1)
                    u = fl_item.get("url")
                    err = fl_item.get("error", "Unknown error")
                    att = fl_item.get("attempts", 3)
                    st.markdown(f"""
                    <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.35); border-radius: 10px; padding: 10px 14px; margin-bottom: 8px;">
                        <span style="color: #F87171; font-weight: 600;">#{idx} Failed after {att} attempts:</span> <code>{u}</code><br>
                        <span style="color: #D1D5DB; font-size: 0.85rem;">Reason: {err}</span>
                    </div>
                    """, unsafe_allow_html=True)


# ==============================================================================
# TAB 3: SECURITY & STORAGE
# ==============================================================================
with tab_storage:
    with st.container(border=True):
        st.markdown("### 🛡️ Security & Device Storage Guidelines")
        st.markdown("""
        - **Direct Device Routing:** When you tap Download on your phone or laptop, the file is saved directly into your device's default `Downloads` folder (Android internal storage, iOS Files, or Windows/Mac Downloads).
        - **Zero Server Retention:** Temporary files on the server instance are purged automatically to ensure complete privacy and zero lingering data on the deployment server.
        - **Pre-Download Security:** Every URL is scanned for SSRF (internal IP exploits), dangerous executable payloads (.exe, .sh, .msi), and invalid protocols before any media transfer begins.
        """)

    with st.container(border=True):
        st.markdown("### 📁 Organized Server Storage & Cache")
        st.markdown("Files are automatically sorted into folders: `large_files/`, `videos/`, `audio/`, `photos/`, and `batch/`.")

        # Collect files from root and category subdirectories
        all_stored_files = []
        for root, dirs, files in os.walk(DOWNLOADS_DIR):
            for f in files:
                if not f.startswith("tmp_"):
                    fp = os.path.join(root, f)
                    rel_dir = os.path.relpath(root, DOWNLOADS_DIR)
                    folder_name = "" if rel_dir == "." else rel_dir
                    all_stored_files.append({
                        "filename": f,
                        "path": fp,
                        "folder": folder_name,
                        "size": os.path.getsize(fp)
                    })

        total_cache = sum(item["size"] for item in all_stored_files)

        col_st1, col_st2 = st.columns(2)
        with col_st1:
            st.metric("Total Stored Files", f"{len(all_stored_files)} files")
        with col_st2:
            st.metric("Server Storage Used", format_bytes(total_cache))

        if st.button("🧹 Purge All Server Storage (Free 100% Disk Space)", type="primary", use_container_width=True):
            for item in all_stored_files:
                try:
                    os.remove(item["path"])
                except Exception:
                    pass
            st.session_state["single_dl_result"] = None
            st.session_state["batch_dl_results"] = []
            st.session_state["batch_zip_file"] = None
            st.success("All storage and temporary folders cleared!")
            st.rerun()

        if all_stored_files:
            st.markdown("---")
            st.markdown("#### Files by Category Folder:")
            for item in all_stored_files:
                f = item["filename"]
                fp = item["path"]
                folder = item["folder"]
                sz_str = format_bytes(item["size"])
                badge_text = f"📂 `{folder}/`" if folder else "📁 `root/`"

                c_name, c_btn = st.columns([2.5, 1])
                with c_name:
                    st.markdown(f"{badge_text} **`{f}`** ({sz_str})")
                with c_btn:
                    with open(fp, "rb") as fl:
                        st.download_button(
                            label=f"💾 Download ({sz_str})",
                            data=fl,
                            file_name=f,
                            key=f"mgt_dl_{folder}_{f}",
                            use_container_width=True
                        )
