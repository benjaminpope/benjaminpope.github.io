 const fs = require('fs');
 const path = require('path');
 const fg = require('fast-glob');
 const cheerio = require('cheerio');
 const mime = require('mime');
 
 function listHtmlFiles(root) {
   return fg.sync(['**/*.html'], { cwd: root, dot: false, onlyFiles: true, absolute: true });
 }
 
 function readHtml(file) {
   const html = fs.readFileSync(file, 'utf8');
   const $ = cheerio.load(html, { decodeEntities: false });
   return { $, html };
 }
 
 function collectImageRefs($) {
   const refs = new Set();
   $('img').each((_, el) => {
     const src = $(el).attr('src');
     if (src) refs.add(src);
   });
   // CSS inline backgrounds
   $('[style]').each((_, el) => {
     const style = $(el).attr('style');
     const m = /url\(([^)]+)\)/i.exec(style || '');
     if (m) refs.add(m[1].replace(/['"]/g, ''));
   });
   // Link rel icons
   $('link[rel="icon"], link[rel="shortcut icon"], link[rel="apple-touch-icon"]').each((_, el) => {
     const href = $(el).attr('href');
     if (href) refs.add(href);
   });
   return Array.from(refs);
 }
 
 function isImageFile(p) {
   const type = mime.getType(p || '') || '';
   return type.startsWith('image/');
 }
 
 function normalizePath(p) {
   return (p || '').replace(/\\/g, '/');
 }
 
 function isRevealHtml($) {
   const hasRevealScript = $('script[src*="reveal"]').length > 0 || $('link[href*="reveal"]').length > 0;
   const hasRevealClass = $('.reveal, .slides').length > 0;
   return hasRevealScript || hasRevealClass;
 }
 
 function collectRevealDeps($) {
   const deps = [];
   $('script[src], link[href]').each((_, el) => {
     const src = el.tagName === 'link' ? el.attribs.href : el.attribs.src;
     if (src && /reveal/i.test(src)) deps.push(src);
   });
   return deps;
 }
 
 function collectLinks($) {
   const links = new Set();
   $('a[href]').each((_, el) => {
     const href = (el.attribs.href || '').trim();
     if (!href) return;
     if (/^https?:\/\//i.test(href)) return; // external
     links.add(href);
   });
   return Array.from(links);
 }
 
 module.exports = {
   listHtmlFiles,
   readHtml,
   collectImageRefs,
   isImageFile,
   normalizePath,
   isRevealHtml,
   collectRevealDeps,
   collectLinks,
 };