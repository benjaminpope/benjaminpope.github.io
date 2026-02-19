 const path = require('path');
 const fs = require('fs');
 const { loadConfig, root } = require('./config');
 const { listHtmlFiles, readHtml, collectLinks } = require('./util');
 
 function main() {
   const { cfg } = loadConfig();
   const files = listHtmlFiles(root);
   const rels = files.map((f) => path.relative(root, f).replace(/\\/g, '/'));
   const indexAbs = path.join(root, 'index.html');
   if (!fs.existsSync(indexAbs)) {
     console.error('index.html not found');
     process.exit(1);
   }
   const { $, html } = readHtml(indexAbs);
   const indexLinks = new Set(collectLinks($).map((l) => l.replace(/^\/?/, '')));
   const orphans = rels.filter((p) => p !== 'index.html' && !indexLinks.has(p) && !indexLinks.has('./' + p));
 
   // Filter likely side projects (shallow-root html not in slides or talks)
   const sideProjects = orphans.filter((p) => !p.startsWith(cfg.paths.slides) && !p.startsWith('talks') && !p.startsWith('sagan_slides') && !p.includes('/'));
 
   let section = $('#side-projects');
   if (!section.length) {
     const container = $('<section id="side-projects"></section>');
     container.append('<h2>Side Projects</h2>');
     $('body').append(container);
     section = container;
   } else {
     // Clear previous list
     section.find('ul').remove();
   }
   const ul = $('<ul></ul>');
   for (const p of sideProjects) {
     const li = $('<li></li>');
     li.append(`<a href="${p}">${p}</a>`);
     ul.append(li);
   }
   section.append(ul);
 
   const out = $.html();
   if (out !== html) fs.writeFileSync(indexAbs, out);
   console.log(`Updated index with ${sideProjects.length} side projects.`);
 }
 
 main();