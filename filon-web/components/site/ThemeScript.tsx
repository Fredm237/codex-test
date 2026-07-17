// Inlined before paint to apply the saved theme and avoid a flash of wrong theme.
export function ThemeScript() {
  const js = `(function(){try{var t=localStorage.getItem('filon-theme');if(t==='dark'||t==='light'){document.documentElement.setAttribute('data-theme',t);}}catch(e){}})();`;
  return <script dangerouslySetInnerHTML={{ __html: js }} />;
}
