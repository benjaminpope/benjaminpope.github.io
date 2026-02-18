 const path = require('path');
 const fs = require('fs');
 const fse = require('fs-extra');
 const { loadConfig, ensureDirs, root } = require('./config');
 const { listHtmlFiles, readHtml, collectImageRefs, isImageFile, normalizePath, isRevealHtml, collectRevealDeps } = require('./util');
 
 function moveFileSafe(fromRel, toRel) {
   const fromAbs = path.join(root, fromRel);
   const toAbs = path.join(root, toRel);
   if (!fs.existsSync(fromAbs)) return false;
   fse.ensureDirSync(path.dirname(toAbs));
   if (fromAbs === toAbs) return false;
   fse.copySync(fromAbs, toAbs, { overwrite: true, errorOnExist: false });
   return true;
 }
 
 function updateHtmlRefs(fileAbs, updates) {
   const html = fs.readFileSync(fileAbs, 'utf8');
   let updated = html;
   for (const { from, to } of updates) {
     // naive replace respecting quotes and plain strings
     const patterns = [from, encodeURI(from)];
     for (const p of patterns) {
       const re = new RegExp(p.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');
       updated = updated.replace(re, to);
     }
   }
   if (updated !== html) fs.writeFileSync(fileAbs, updated);
 }
 
 function main() {
   const { cfg } = loadConfig();
   ensureDirs(cfg.paths);
 
   const htmlFiles = listHtmlFiles(root);
   const imageUpdates = [];
 
   for (const file of htmlFiles) {
     const rel = path.relative(root, file).replace(/\\/g, '/');
     const { $ } = readHtml(file);
 
     // Images: move to top-level images and update refs
     const refs = collectImageRefs($);
     const thisFileUpdates = [];
     for (const ref of refs) {
       const src = normalizePath(ref);
       if (!isImageFile(src)) continue;
       if (src.startsWith('data:')) continue;
       const srcAbs = path.resolve(path.dirname(file), src);
       const srcRel = path.relative(root, srcAbs).replace(/\\/g, '/');
       const basename = path.basename(srcRel);
       const targetRel = `${cfg.paths.images}/${basename}`;
       if (srcRel !== targetRel) {
         const moved = moveFileSafe(srcRel, targetRel);
         if (moved) {
           thisFileUpdates.push({ from: src, to: path.relative(path.dirname(rel), targetRel).replace(/\\/g, '/') });
           imageUpdates.push({ from: srcRel, to: targetRel, in: rel });
         }
       }
     }
 
     // Reveal deps: centralize to slides/revealjs and update refs to use basename
     if (isRevealHtml($)) {
       const deps = collectRevealDeps($);
       for (const d of deps) {
         const depAbs = path.resolve(path.dirname(file), d);
         const depRel = path.relative(root, depAbs).replace(/\\/g, '/');
         const base = path.basename(depRel);
         const targetRel = `${cfg.paths.slidesReveal}/${base}`;
         const copied = moveFileSafe(depRel, targetRel);
         if (copied) {
           const toHref = path.relative(path.dirname(rel), targetRel).replace(/\\/g, '/');
           thisFileUpdates.push({ from: d, to: toHref });
         }
       }
     }
 
     // Write updates for this html
     if (thisFileUpdates.length) updateHtmlRefs(file, thisFileUpdates);
   }
 
   console.log('Apply complete. Updated image and reveal.js references.');
 }
 
 main();