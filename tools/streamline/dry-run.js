 const path = require('path');
 const fs = require('fs');
 const fse = require('fs-extra');
 const { loadConfig, ensureDirs, root } = require('./config');
 const { listHtmlFiles, readHtml, collectImageRefs, isImageFile, normalizePath, isRevealHtml, collectRevealDeps, collectLinks } = require('./util');
 
 function writeReport(name, data) {
   const out = path.join(root, 'tools/reports', `${name}.json`);
   fse.ensureDirSync(path.dirname(out));
   fs.writeFileSync(out, JSON.stringify(data, null, 2));
   console.log(`Report written: ${path.relative(root, out)}`);
 }
 
 function main() {
   const { cfg } = loadConfig();
   ensureDirs(cfg.paths);
 
   const htmlFiles = listHtmlFiles(root);
 
  const imageMoves = [];
  const collisionMap = new Map(); // targetRel -> Set(fromRel)
   const slidePlans = [];
   const pageLinks = new Map();
 
   // Build set of all html files relative paths
   const allHtmlRel = new Set(htmlFiles.map((abs) => path.relative(root, abs).replace(/\\/g, '/')));
 
   for (const file of htmlFiles) {
     const rel = path.relative(root, file).replace(/\\/g, '/');
     const { $ } = readHtml(file);
 
     // Collect images
     const refs = collectImageRefs($);
     for (const ref of refs) {
       const src = normalizePath(ref);
       if (!isImageFile(src)) continue;
       // skip data URLs
       if (src.startsWith('data:')) continue;
       const srcAbs = path.resolve(path.dirname(file), src);
       const srcRel = path.relative(root, srcAbs).replace(/\\/g, '/');
       const basename = path.basename(srcRel);
       const targetRel = `${cfg.paths.images}/${basename}`;
       // track collisions by basename/target
       if (!collisionMap.has(targetRel)) collisionMap.set(targetRel, new Set());
       collisionMap.get(targetRel).add(srcRel);
       if (srcRel !== targetRel) {
         imageMoves.push({ from: srcRel, to: targetRel, in: rel });
       }
     }
 
     // Slides and reveal deps
     const isReveal = isRevealHtml($);
     if (isReveal) {
       const deps = collectRevealDeps($);
       slidePlans.push({ file: rel, deps });
     }
 
     // Links for orphan detection
     pageLinks.set(rel, collectLinks($));
   }
 
   // Orphan pages: those not reachable from index.html (direct only)
   const indexLinks = new Set((pageLinks.get('index.html') || []).map((l) => l.replace(/^\/?/, '')));
   const orphans = Array.from(allHtmlRel).filter((p) => p !== 'index.html' && !indexLinks.has(p) && !indexLinks.has('./' + p));
 
  const collisions = Array.from(collisionMap.entries())
    .filter(([, set]) => set.size > 1)
    .map(([target, set]) => ({ target, sources: Array.from(set) }));
  writeReport('images', { plannedMoves: imageMoves, collisions });
   writeReport('slides', { revealPages: slidePlans });
   writeReport('orphans', { orphans });
   writeReport('contacts', { person: cfg.person, social: cfg.social });
 
  // Console summary
  console.log('--- Streamline Dry-Run Summary ---');
  console.log(`HTML pages scanned: ${htmlFiles.length}`);
  console.log(`Planned image moves: ${imageMoves.length}`);
  console.log(`Potential filename collisions: ${collisions.length}`);
  console.log(`Reveal.js slide pages: ${slidePlans.length}`);
  console.log(`Orphan pages (not linked from index.html): ${orphans.length}`);
  console.log('Reports written under tools/reports/.');
 }
 
 main();