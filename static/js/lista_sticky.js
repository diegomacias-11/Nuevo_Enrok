(function () {
  const root = document.documentElement;
  const stack = document.querySelector(".lista-sticky-stack");
  const headContainer = document.querySelector(".lista-head-container");
  const headScroll = document.querySelector(".lista-head-scroll");
  const headInner = document.querySelector(".lista-head-scroll-inner");
  const headViewport = document.querySelector(".lista-head-viewport");
  const headTable = document.querySelector(".lista-head-table");
  const headThead = headTable ? headTable.querySelector("thead") : null;
  const bodyContainer = document.querySelector(".lista-table-container");
  const bodyTable = document.querySelector(".lista-body-table");
  const bodyThead = bodyTable ? bodyTable.querySelector("thead") : null;

  if (!root || !stack || !headContainer || !headScroll || !headInner || !headViewport || !headTable || !headThead || !bodyContainer || !bodyTable || !bodyThead) {
    return;
  }

  let syncingFromHead = false;
  let syncingFromBody = false;

  const buildColGroup = (widths) => {
    const colgroup = document.createElement("colgroup");
    widths.forEach((width) => {
      const col = document.createElement("col");
      col.style.width = `${width}px`;
      colgroup.appendChild(col);
    });
    return colgroup;
  };

  const clearHeadColgroups = () => {
    Array.from(headTable.querySelectorAll(":scope > colgroup")).forEach((node) => node.remove());
  };

  const clearBodyColgroups = () => {
    Array.from(bodyTable.querySelectorAll(":scope > colgroup")).forEach((node) => node.remove());
  };

  const syncStackHeight = () => {
    const styles = window.getComputedStyle(stack);
    const marginBottom = parseFloat(styles.marginBottom || "0") || 0;
    const height = Math.ceil(stack.getBoundingClientRect().height + marginBottom);
    root.style.setProperty("--lista-stack-height", `${height}px`);
  };

  const syncHeaderStructure = () => {
    headThead.innerHTML = bodyThead.innerHTML;
  };

  const syncHeaderMetrics = () => {
    const sourceThs = Array.from(bodyThead.querySelectorAll("th"));
    if (!sourceThs.length) {
      headContainer.hidden = true;
      headContainer.setAttribute("aria-hidden", "true");
      bodyTable.classList.remove("lista-head-source-hidden");
      clearHeadColgroups();
      clearBodyColgroups();
      root.style.setProperty("--lista-head-table-height", "0px");
      root.style.setProperty("--lista-head-scroll-height", "0px");
      return;
    }

    syncHeaderStructure();

    const widths = sourceThs.map((th) => Math.round(th.getBoundingClientRect().width));
    clearHeadColgroups();
    clearBodyColgroups();
    headTable.prepend(buildColGroup(widths));
    bodyTable.prepend(buildColGroup(widths));

    const scrollWidth = Math.ceil(bodyTable.scrollWidth);
    const clientWidth = Math.ceil(bodyContainer.clientWidth);
    const hasOverflow = scrollWidth > clientWidth + 1;
    const visibleWidth = Math.max(scrollWidth, clientWidth);

    headTable.style.width = `${scrollWidth}px`;
    headInner.style.width = `${visibleWidth}px`;
    headScroll.hidden = false;
    headScroll.setAttribute("aria-hidden", "false");
    headContainer.hidden = false;
    headContainer.setAttribute("aria-hidden", "false");
    bodyTable.classList.add("lista-head-source-hidden");

    const scrollHeight = Math.ceil(headScroll.getBoundingClientRect().height);
    const headerHeight = Math.ceil(headViewport.getBoundingClientRect().height);
    root.style.setProperty("--lista-head-scroll-height", `${scrollHeight}px`);
    root.style.setProperty("--lista-head-table-height", `${headerHeight}px`);
  };

  const syncCloneScroll = () => {
    headTable.style.transform = `translateX(-${bodyContainer.scrollLeft}px)`;
    if (!syncingFromBody) {
      headScroll.scrollLeft = bodyContainer.scrollLeft;
    }
  };

  const onBodyScroll = () => {
    if (syncingFromHead) return;
    syncingFromBody = true;
    syncCloneScroll();
    window.requestAnimationFrame(() => {
      syncingFromBody = false;
    });
  };

  const onHeadScroll = () => {
    if (syncingFromBody) return;
    syncingFromHead = true;
    bodyContainer.scrollLeft = headScroll.scrollLeft;
    headTable.style.transform = `translateX(-${headScroll.scrollLeft}px)`;
    window.requestAnimationFrame(() => {
      syncingFromHead = false;
    });
  };

  const syncAll = () => {
    syncStackHeight();
    syncHeaderMetrics();
    syncCloneScroll();
  };

  const scheduleSync = () => window.requestAnimationFrame(syncAll);

  if ("ResizeObserver" in window) {
    const observer = new ResizeObserver(scheduleSync);
    observer.observe(stack);
    observer.observe(bodyContainer);
    observer.observe(bodyTable);
  }

  bodyContainer.addEventListener("scroll", onBodyScroll, { passive: true });
  headScroll.addEventListener("scroll", onHeadScroll, { passive: true });
  window.addEventListener("resize", scheduleSync);
  window.addEventListener("load", scheduleSync);
  document.addEventListener("DOMContentLoaded", scheduleSync);
  scheduleSync();
})();
