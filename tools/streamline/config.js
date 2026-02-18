 const fs = require('fs');
 const path = require('path');
 const fse = require('fs-extra');
 
 const root = path.resolve(__dirname, '../../');
 const configPath = path.join(root, 'site-config.json');
 
 function loadConfig() {
   const raw = fs.readFileSync(configPath, 'utf8');
   const cfg = JSON.parse(raw);
   // Normalize paths
   const norm = (p) => p.replace(/\\/g, '/').replace(/^\//, '').replace(/\/$/, '');
   cfg.paths.images = norm(cfg.paths.images || 'images');
   cfg.paths.slides = norm(cfg.paths.slides || 'slides');
   cfg.paths.slidesReveal = norm(cfg.paths.slidesReveal || `${cfg.paths.slides}/revealjs`);
   return { cfg, root };
 }
 
 function ensureDirs(paths) {
   [paths.images, paths.slides, paths.slidesReveal, 'tools/reports'].forEach((p) => {
     fse.ensureDirSync(path.join(root, p));
   });
 }
 
 module.exports = { loadConfig, ensureDirs, root };