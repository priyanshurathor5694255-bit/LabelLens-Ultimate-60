import json, time
from pathlib import Path
import streamlit as st
from PIL import Image
import pandas as pd

from modules.ui import inject_css, hero, metric_card, feature_card
from modules.ocr_engine import run_ocr, extract_fields, terminology_report
from modules.advanced_local import prepare, diagnostics, evidence_overlay, font_pixels, image_hash
from modules.compliance import evaluate, stats
from modules.storage import save_scan, history_df, upsert_product, find_product, product_df, audit_df, add_audit
from modules.reports import make_pdf, make_docx
from modules.export_tools import csv_bytes, xlsx_bytes
from modules.advanced_compliance import evaluate_full
from modules.feature60 import (
    normalize_visual, denoise, adaptive_threshold, deskew, perspective_correct_auto,
    detect_regions, crop_regions, qr_codes, barcode_codes, text_scale_calibration,
    physical_text_height, multilingual_reader, field_confidence, corrections,
    rule_pack_manifest, image_fingerprint, save_evidence, evidence_bundle,
    compare_scans, reviewer_note
)

st.set_page_config(page_title='LabelLens Ultimate 60', page_icon='🔎', layout='wide')
if 'page' not in st.session_state: st.session_state.page='Home'
if 'last' not in st.session_state: st.session_state.last=None
if 'lang' not in st.session_state: st.session_state.lang='en'
if 'theme' not in st.session_state: st.session_state.theme='dark'

inject_css(st.session_state.theme)

PAGES=['Home','Scan','Batch','Dashboard','Products','Reports','Review','Settings','Features']
with st.sidebar:
    st.markdown('''<div class="brand-row"><div class="brand-mark">⌕</div><div><div class="brand-name">LabelLens</div><div class="brand-sub">AI-assisted label inspection</div></div></div>''', unsafe_allow_html=True)
    for p in PAGES:
        icon={'Home':'⌂','Scan':'⌕','Batch':'▦','Dashboard':'◈','Products':'▣','Reports':'▤','Review':'✓','Settings':'⚙','Features':'✦'}[p]
        if st.button(f'{icon}  {p}', use_container_width=True, key='nav_'+p): st.session_state.page=p
    st.divider()
    st.caption('Appearance')
    theme_label=st.radio('Theme', ['Dark','Light'], index=0 if st.session_state.theme=='dark' else 1, horizontal=True, label_visibility='collapsed')
    new_theme='dark' if theme_label=='Dark' else 'light'
    if new_theme != st.session_state.theme:
        st.session_state.theme=new_theme
        st.rerun()
    st.caption('60-feature build • local-first • evidence-first')

def result_status(s):
    return 'PASS' if s['issues']==0 and s['review']==0 else ('REVIEW' if s['issues']==0 else 'POTENTIAL NON-COMPLIANCE')

def run_multilang_ocr(image, languages):
    try:
        reader=multilingual_reader(languages)
        result=reader.readtext(__import__('numpy').array(image.convert('RGB')))
        return [{'text':str(t),'confidence':float(c),'box':b} for b,t,c in result], None
    except Exception as e:
        return [], f'Multilingual OCR unavailable: {e}'

def inspect_images(images, category, languages):
    all_items=[]; diags=[]; qr=[]; bar=[]; processed=[]
    for original in images:
        im=prepare(original)
        # deterministic preprocessing chain: orientation, denoise, illumination normalization, deskew
        im=normalize_visual(im)
        im=denoise(im)
        im=deskew(im)
        corrected, corrected_ok=perspective_correct_auto(im)
        if corrected_ok: im=corrected
        processed.append(im)
        diags.append(diagnostics(im))
        if languages == ['en']:
            items,e=run_ocr(im)
        else:
            items,e=run_multilang_ocr(im,languages)
        if e: st.warning(e)
        all_items.extend(items)
        qr.extend(qr_codes(im)); bar.extend(barcode_codes(im))
    fields, raw=extract_fields(all_items)
    d=diags[0] if diags else {}
    fp=font_pixels(all_items)
    rows=evaluate(fields,d,fp)
    # Full rule-pack adds evidence-oriented checks without replacing the original compact evaluator.
    full=evaluate_full(fields,category,d,fp)
    # Keep both: compact rows are the scoring basis; full rows are displayed as expanded evidence.
    s=stats(rows)
    return {'images':processed,'items':all_items,'fields':fields,'raw':raw,'rows':rows,'full_rows':full,'stats':s,
            'status':result_status(s),'category':category,'diag':d,'font':fp,'qr':qr,'bar':bar,
            'field_conf':field_confidence(fields,all_items),'regions':detect_regions(processed[0]) if processed else [],
            'fingerprint':image_fingerprint(processed[0]) if processed else ''}

if st.session_state.page=='Home':
    hero('Inspect labels. Prove every decision.', 'LabelLens 60 combines OCR, real-world terminology intelligence, image-quality gating, calibrated visual checks, code detection, evidence storage, repeat inspection and professional reporting.')
    cols=st.columns(4)
    for c,v,l in zip(cols,['60','3','100+','0'],['Implemented feature areas','Decision states','Batch image workflow','Fake external integrations']):
        with c: metric_card(v,l)
    st.markdown('<div class="section">The complete inspection workflow</div>', unsafe_allow_html=True)
    fs=[('📷','Capture','Upload, camera capture, multi-image and format handling.'),('🧠','Understand','OCR, multilingual option, normalization and field extraction.'),('🧭','Improve evidence','Denoise, deskew, perspective, adaptive threshold and quality diagnostics.'),('🔎','Inspect','Rules, score, calibrated text measurement and review states.'),('🧾','Prove','OCR overlay, codes, fingerprints and evidence bundles.'),('📊','Operate','Batch, history, repository, dashboard, review and exports.')]
    for start in range(0,6,3):
        cs=st.columns(3)
        for c,(i,t,d) in zip(cs,fs[start:start+3]):
            with c: feature_card(i,t,d)
    st.info('Important: advanced measurements return INDETERMINATE when calibration or model evidence is missing. LabelLens never invents a legal measurement.')

elif st.session_state.page=='Scan':
    hero('Scan product', 'Capture one or several sides of a package. LabelLens builds one evidence-backed inspection from the submitted images.')
    c1,c2,c3=st.columns(3)
    with c1: category=st.selectbox('Product category',['food','cosmetic','textile','household','other'])
    with c2: lang_label=st.selectbox('OCR language',['English','English + Hindi','English + Marathi','English + Tamil','English + Telugu'])
    with c3: source=st.radio('Capture source',['Upload','Camera'],horizontal=True)
    lang_map={'English':['en'],'English + Hindi':['en','hi'],'English + Marathi':['en','mr'],'English + Tamil':['en','ta'],'English + Telugu':['en','te']}
    languages=lang_map[lang_label]
    uploads=[]
    if source=='Upload':
        uploads=st.file_uploader('Upload front / back / side images',type=['jpg','jpeg','png','webp'],accept_multiple_files=True)
    else:
        cam=st.camera_input('Take a label photo')
        if cam: uploads=[cam]
    if uploads:
        st.caption(f'{len(uploads)} image(s) selected')
        st.image([Image.open(x) for x in uploads],width=210)
    if st.button('🚀 Run complete 60-feature inspection', type='primary', disabled=not uploads, use_container_width=True):
        with st.spinner('Preparing evidence → OCR → codes → rules → report data...'):
            r=inspect_images([Image.open(x) for x in uploads],category,languages)
            product=r['fields'].get('product_name',{}).get('value','Unknown') or 'Unknown'
            rec=save_scan(product,category,r['stats'],r['status'])
            upsert_product(product,category,r['stats']['score'],r['fields'])
            add_audit('complete_inspection',{'scan_id':rec['scan_id'],'fingerprint':r['fingerprint'],'images':len(uploads)})
            save_evidence(rec['scan_id'],r['images'][0],{'scan_id':rec['scan_id'],'product':product,'category':category,'status':r['status'],'score':r['stats']['score'],'full_rows':r['full_rows'],'codes':r['qr']+r['bar']})
            r.update(product=product,scan_id=rec['scan_id'],image=r['images'][0],images_count=len(uploads),rule_manifest=rule_pack_manifest())
            st.session_state.last=r
        st.success(f"Inspection {rec['scan_id']} complete")
    r=st.session_state.last
    if r:
        st.markdown('<div class="section">Inspection result</div>',unsafe_allow_html=True)
        cs=st.columns(5)
        vals=[f"{r['stats']['score']}%",r['stats']['passed'],r['stats']['review'],r['stats']['issues'],r['images_count']]
        labs=['Score','Passed','Review','Potential issues','Images']
        for c,v,l in zip(cs,vals,labs):
            with c: metric_card(v,l)
        st.write(f"Decision: **{r['status']}**")
        if r['qr'] or r['bar']:
            st.success(f"Codes detected: {len(r['qr'])} QR + {len(r['bar'])} barcode")
            st.json(r['qr']+r['bar'])
        tabs=st.tabs(['Evidence','Compliance','Extracted data','Visual intelligence','Calibration','History & review','Export'])
        with tabs[0]:
            st.image(evidence_overlay(r['image'],r['items']),use_container_width=True)
            st.caption('Every OCR item is shown in its source image region. The SHA-256 fingerprint identifies the primary evidence image.')
            st.code(r['fingerprint'])
            boxes=r['regions']; st.write(f'Local package/label region proposals: {len(boxes)}')
            if boxes: st.image([r['image'].crop(b) for b in boxes[:12]],width=150)
        with tabs[1]:
            df=pd.DataFrame(r['rows']); st.dataframe(df,use_container_width=True,hide_index=True)
            st.markdown('#### Expanded rule evidence')
            st.dataframe(pd.DataFrame(corrections(r['full_rows'])),use_container_width=True,hide_index=True)
            st.caption(f"Rule pack: {r['rule_manifest']['name']} • {r['rule_manifest']['version']}")
        with tabs[2]:
            st.text_area('OCR text',r['raw'],height=180)
            st.dataframe(pd.DataFrame(terminology_report(r['raw'])),use_container_width=True,hide_index=True)
            st.dataframe(pd.DataFrame([{'field':k,'found':v.get('found'),'value':v.get('value'),'matched_term':v.get('matched_term'),'confidence':r['field_conf'].get(k)} for k,v in r['fields'].items()]),use_container_width=True,hide_index=True)
        with tabs[3]:
            st.write(r['diag']); st.write(r['font'])
            st.image(adaptive_threshold(r['image']),caption='Adaptive-threshold evidence preview',use_container_width=True)
            st.caption('The visual pipeline uses local preprocessing. Region proposals are deterministic CV; they are not presented as a trained AI object detector.')
        with tabs[4]:
            st.markdown('#### Physical font measurement')
            ref_px=st.number_input('Known reference length in pixels',min_value=0.0,value=0.0,step=1.0)
            ref_mm=st.number_input('That reference length in millimetres',min_value=0.0,value=0.0,step=0.1)
            if ref_px>0 and ref_mm>0:
                cal=text_scale_calibration(ref_px,ref_mm); est=physical_text_height(r['font'].get('pixel_height',0),cal)
                st.success(f"Calibrated estimate: {est['mm']} mm median text height")
            else:
                st.warning('No calibration supplied → physical size remains INDETERMINATE.')
        with tabs[5]:
            h=history_df(); prev=None
            if not h.empty:
                same=h[(h.product==r['product']) & (h.scan_id!=r['scan_id'])]
                if not same.empty: prev=float(same.iloc[0].score)
            st.json(compare_scans(prev,r['stats']['score']))
            note=st.text_area('Reviewer note',key='review_note')
            reviewer=st.text_input('Reviewer name','Human reviewer')
            if st.button('Save reviewer annotation') and note.strip():
                reviewer_note(r['scan_id'],note,reviewer); add_audit('review_note_added',{'scan_id':r['scan_id']}); st.success('Review annotation saved locally.')
        with tabs[6]:
            pdf=make_pdf(r['product'],r['category'],r['stats'],r['rows'],r['image'])
            docx=make_docx(r['product'],r['category'],r['stats'],r['rows'],r['image'])
            st.download_button('PDF report',pdf.read_bytes(),pdf.name,'application/pdf')
            st.download_button('DOCX report',docx.read_bytes(),docx.name,'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            st.download_button('Excel checks',xlsx_bytes(r['rows']),'inspection.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            st.download_button('JSON evidence',json.dumps({'scan_id':r['scan_id'],'product':r['product'],'category':r['category'],'status':r['status'],'score':r['stats']['score'],'fields':r['fields'],'rules':r['full_rows'],'fingerprint':r['fingerprint'],'codes':r['qr']+r['bar']},indent=2).encode(),'inspection.json','application/json')
            bundle=evidence_bundle(r['scan_id'])
            if bundle: st.download_button('Evidence ZIP bundle',bundle,f"{r['scan_id']}_evidence.zip",'application/zip')

elif st.session_state.page=='Batch':
    hero('Batch inspection','Process many independent product images sequentially, with the same deterministic pipeline used by Scan.')
    cat=st.selectbox('Category',['food','cosmetic','textile','household','other'],key='batchcat')
    ups=st.file_uploader('Choose product images',type=['jpg','jpeg','png','webp'],accept_multiple_files=True,key='batchfiles')
    if ups: st.info(f'{len(ups)} images selected. The workflow supports 100+ uploaded images; runtime depends on OCR workload.')
    if st.button('Run batch',type='primary',disabled=not ups):
        out=[]; bar=st.progress(0)
        for n,u in enumerate(ups,1):
            r=inspect_images([Image.open(u)],cat,['en']); out.append({'File':u.name,'Product':r['fields'].get('product_name',{}).get('value','Unknown'),'Score':r['stats']['score'],'Status':r['status'],'Issues':r['stats']['issues'],'Review':r['stats']['review']}); bar.progress(n/len(ups))
        st.session_state.batch=pd.DataFrame(out)
    if 'batch' in st.session_state:
        st.dataframe(st.session_state.batch,use_container_width=True,hide_index=True)
        st.download_button('Batch CSV',st.session_state.batch.to_csv(index=False).encode(),'batch.csv','text/csv')

elif st.session_state.page=='Dashboard':
    hero('Inspection dashboard','Track outcomes, trends, categories and evidence-backed review workload.')
    df=history_df()
    if df.empty: st.info('No inspections yet.')
    else:
        cols=st.columns(5)
        vals=[len(df),(df.status=='PASS').sum(),(df.status=='REVIEW').sum(),(df.status=='POTENTIAL NON-COMPLIANCE').sum(),round(df.score.mean(),1)]
        for c,v,l in zip(cols,vals,['Total','Pass','Review','Potential issues','Avg score']):
            with c: metric_card(v,l)
        st.dataframe(df.head(100),use_container_width=True,hide_index=True)
        x=df.copy(); x['date']=pd.to_datetime(x.timestamp).dt.date
        st.line_chart(x.groupby('date').score.mean())
        st.dataframe(df.groupby('category').score.mean().reset_index(),use_container_width=True,hide_index=True)

elif st.session_state.page=='Products':
    hero('Product repository','Local repeat-inspection catalogue with exact identity matching and score history.')
    name=st.text_input('Search product')
    if name:
        p=find_product(name)
        if p: st.success(f"Existing product • {p['category']} • score {p['score']}% • updated {p['updated']}")
        else: st.info('No exact product match.')
    pdf=product_df()
    if not pdf.empty: st.dataframe(pdf.drop(columns=['fields'],errors='ignore'),use_container_width=True,hide_index=True)

elif st.session_state.page=='Reports':
    hero('Reports','Generated inspection documents stored locally in the reports folder.')
    files=sorted(Path('reports').glob('*'),reverse=True)
    if not files: st.info('Run an inspection to generate a report.')
    for p in files[:50]:
        mime='application/pdf' if p.suffix=='.pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        st.download_button(('📄 ' if p.suffix=='.pdf' else '📝 ')+p.name,p.read_bytes(),p.name,mime,key=str(p))

elif st.session_state.page=='Review':
    hero('Human review queue','Uncertain cases remain visible for human verification instead of being silently forced into a pass/fail answer.')
    df=history_df()
    if df.empty: st.info('Nothing to review.')
    else:
        review=df[df.status=='REVIEW']; st.dataframe(review,use_container_width=True,hide_index=True)
        st.caption('Reviewer annotations are stored locally in data/review_notes.json.')
        p=Path('data/review_notes.json')
        if p.exists(): st.dataframe(pd.DataFrame(json.loads(p.read_text())),use_container_width=True,hide_index=True)

elif st.session_state.page=='Settings':
    hero('Settings','Local-first controls. No external account, cloud database or paid API is silently required.')
    st.selectbox('Role',['Inspector','Reviewer','Admin','Manufacturer'])
    st.selectbox('Interface language',['English','Hindi + English'])
    st.checkbox('Require human verification for REVIEW',True)
    st.checkbox('Save scan history',True)
    st.checkbox('Save evidence images locally',True)
    st.info('Optional external services can be connected later, but this build does not pretend an unavailable service is working.')
    st.json(rule_pack_manifest())

elif st.session_state.page=='Features':
    hero('60 implemented feature areas','A transparent feature inventory. Advanced features fail safely to REVIEW/INDETERMINATE rather than manufacturing evidence.')
    groups={
    '1–10 • Capture & OCR':['1 Single image upload','2 Multiple image upload','3 JPG/PNG/WEBP support','4 Image preview','5 EXIF orientation correction','6 Image resizing','7 Contrast enhancement','8 Sharpness enhancement','9 EasyOCR text extraction','10 OCR confidence'],
    '11–20 • Understanding':['11 Case normalization','12 MRP normalization','13 Synonym dictionary','14 Abbreviation handling','15 Field extraction','16 Value extraction','17 Terminology report','18 Product-name heuristic','19 Configurable multilingual OCR','20 Per-field confidence'],
    '21–30 • Inspection':['21 Category selection','22 Rule-pack evaluation','23 Required/optional logic','24 PASS state','25 REVIEW state','26 Potential non-compliance state','27 Compliance score','28 Image-quality gate','29 Sharpness metric','30 Glare/darkness diagnostics'],
    '31–40 • Evidence & visual intelligence':['31 Pixel text-height measurement','32 OCR evidence overlay','33 Scan ID','34 Timestamp','35 Scan history','36 Product repository','37 Duplicate recognition','38 Audit event log','39 Batch processing','40 CSV/Excel export'],
    '41–50 • Advanced local vision':['41 Camera capture','42 Illumination normalization','43 Conservative denoise','44 Adaptive thresholding','45 Deskewing','46 Automatic perspective correction','47 Package/label region proposals','48 QR decoding','49 1-D barcode decoding (optional local zbar)','50 Explicit pixels-per-mm calibration'],
    '51–60 • Advanced compliance & operations':['51 Calibrated physical text-height estimate','52 Multilingual OCR packs','53 Evidence confidence aggregation','54 Corrective suggestions','55 Versioned rule-pack manifest','56 SHA-256 evidence fingerprint','57 Local evidence vault','58 Portable evidence ZIP','59 Repeat-inspection score delta','60 Human reviewer annotations']}
    for g,items in groups.items():
        st.markdown(f'<div class="section">{g}</div>',unsafe_allow_html=True)
        for i in range(0,len(items),3):
            cs=st.columns(3)
            for c,item in zip(cs,items[i:i+3]):
                with c: feature_card('✓',item,'Implemented in this build.')

st.caption('LabelLens Ultimate 60 • AI-assisted inspection • Results are decision support, not a legal determination.')
