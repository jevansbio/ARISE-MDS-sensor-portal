import { useEffect, useState } from "react";

export function useReadDocumentTitle() {
  const [title, setTitle] = useState(document.title);
  useEffect(() => {
    const titleElem = document.querySelector('title');
    if (!titleElem) return;
    const observer = new MutationObserver(function (mutations) {
      setTitle(mutations[0].target.textContent ?? '');
    });
    observer.observe(
      titleElem,
      { subtree: true, characterData: true, childList: true }
    );
    return () => {
      observer.disconnect();
    }
  }, [])

  return title;
}