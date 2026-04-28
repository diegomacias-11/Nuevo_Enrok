(function () {
  const raw = document.getElementById("citas-dashboard-data");
  if (!raw || typeof Chart === "undefined") return;

  const data = JSON.parse(raw.textContent || "{}");
  const baseBlue = "#003b71";
  const accentBlue = "#6ea3cf";
  const numberFormat = new Intl.NumberFormat("es-MX", {
    maximumFractionDigits: 0
  });

  const toRgb = (color) => {
    const clean = color.replace("#", "");
    const num = parseInt(clean, 16);
    return {
      r: (num >> 16) & 255,
      g: (num >> 8) & 255,
      b: num & 255
    };
  };

  const mix = (a, b, t) => Math.round(a + (b - a) * t);
  const base = toRgb(baseBlue);
  const accent = toRgb(accentBlue);

  const buildShades = (count, spread = 0.85) => {
    return Array.from({ length: count }, (_, i) => {
      if (count === 1) return `rgb(${base.r}, ${base.g}, ${base.b})`;
      const t = (i / (count - 1)) * spread;
      return `rgb(${mix(base.r, accent.r, t)}, ${mix(base.g, accent.g, t)}, ${mix(base.b, accent.b, t)})`;
    });
  };

  const applyFilter = (field, value) => {
    if (!field || value === undefined || value === null) return;
    const url = new URL(window.location.href);
    if (url.searchParams.get(field) === String(value)) {
      url.searchParams.delete(field);
    } else {
      url.searchParams.set(field, value);
    }
    window.location.href = url.toString();
  };

  const fixedLabels = {
    id: "fixedLabels",
    afterDatasetsDraw(chart) {
      const ctx = chart.ctx;
      const dataset = chart.data.datasets[0] || {};
      const dataArr = dataset.data || [];
      if (!dataArr.length) return;

      ctx.save();
      ctx.fillStyle = baseBlue;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.font = "600 11px Arial";

      if (chart.config.type === "bar") {
        const meta = chart.getDatasetMeta(0);
        meta.data.forEach((bar, i) => {
          const value = Number(dataArr[i] || 0);
          if (!value) return;
          const pos = bar.tooltipPosition();
          if (chart.options.indexAxis === "y") {
            ctx.textAlign = "left";
            ctx.fillText(value, pos.x + 8, pos.y);
          } else {
            ctx.textAlign = "center";
            ctx.fillText(value, pos.x, pos.y - 10);
          }
        });
      }

      if (chart.config.type === "doughnut") {
        const total = dataArr.reduce((sum, value) => sum + Number(value || 0), 0);
        const meta = chart.getDatasetMeta(0);
        const chartArea = chart.chartArea;
        const items = [];

        meta.data.forEach((arc, i) => {
          const value = Number(dataArr[i] || 0);
          if (!value) return;
          const pct = total > 0 ? (value / total) * 100 : 0;
          const angle = (arc.startAngle + arc.endAngle) / 2;
          const side = Math.cos(angle) >= 0 ? 1 : -1;
          const anchor = {
            x: arc.x + Math.cos(angle) * arc.outerRadius,
            y: arc.y + Math.sin(angle) * arc.outerRadius
          };
          const y = arc.y + Math.sin(angle) * (arc.outerRadius + 18);
          items.push({
            side,
            anchor,
            y,
            label: chart.data.labels[i] || "",
            line2: `${numberFormat.format(value)} (${pct.toFixed(2)}%)`
          });
        });

        const minGap = 34;
        const left = items.filter((i) => i.side < 0).sort((a, b) => a.y - b.y);
        const right = items.filter((i) => i.side > 0).sort((a, b) => a.y - b.y);

        const adjust = (arr) => {
          let prev = null;
          const top = chartArea.top + 28;
          const bottom = chartArea.bottom - 28;
          arr.forEach((it) => {
            let y = Math.max(it.y, top);
            if (prev !== null && y - prev < minGap) y = prev + minGap;
            if (y > bottom) y = bottom;
            it.y = y;
            prev = y;
          });
        };
        adjust(left);
        adjust(right);

        ctx.save();
        ctx.beginPath();
        const clipPad = 10;
        ctx.rect(
          chartArea.left - clipPad,
          chartArea.top - clipPad,
          (chartArea.right - chartArea.left) + (clipPad * 2),
          (chartArea.bottom - chartArea.top) + (clipPad * 2)
        );
        ctx.clip();
        ctx.strokeStyle = "#4e7fae";
        ctx.lineWidth = 1;

        const drawSide = (arr, side) => {
          const textAlign = side > 0 ? "right" : "left";
          const textX = side > 0 ? (chartArea.right - 10) : (chartArea.left + 10);
          const textGap = 8;
          arr.forEach((it) => {
            const midX = Math.max(chartArea.left + 2, Math.min(it.anchor.x + side * 16, chartArea.right - 2));
            const endX = Math.max(chartArea.left + 10, Math.min(textX, chartArea.right - 10));
            ctx.beginPath();
            ctx.moveTo(it.anchor.x, it.anchor.y);
            ctx.lineTo(midX, it.y);
            const lineEndX = endX + (side > 0 ? -textGap : textGap);
            ctx.lineTo(lineEndX, it.y);
            ctx.stroke();

            ctx.textAlign = textAlign;
            ctx.fillStyle = baseBlue;
            ctx.font = "600 11px Arial";
            const maxTextWidth = (chartArea.right - chartArea.left) * 0.35;
            const label = ctx.measureText(it.label).width > maxTextWidth ? `${it.label.slice(0, 12)}...` : it.label;
            const textXAdj = endX + (side > 0 ? -2 : 2);
            ctx.fillText(label, textXAdj, it.y - 8);
            ctx.font = "500 10px Arial";
            const line2 = ctx.measureText(it.line2).width > maxTextWidth ? `${it.line2.slice(0, 12)}...` : it.line2;
            ctx.fillText(line2, textXAdj, it.y + 8);
          });
        };

        drawSide(left, -1);
        drawSide(right, 1);
        ctx.restore();
      }

      ctx.restore();
    }
  };

  const makeOptions = (field, values, horizontal) => ({
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: horizontal ? "y" : "x",
    onClick(event, elements) {
      if (!elements.length) return;
      const index = elements[0].index;
      applyFilter(field, values[index]);
    },
    plugins: {
      legend: { display: false },
      tooltip: { enabled: false }
    },
    scales: {
      x: {
        ticks: {
          color: baseBlue,
          font: { weight: "600" }
        }
      },
      y: {
        beginAtZero: true,
        grace: "10%",
        ticks: {
          color: baseBlue,
          font: { weight: "600" },
          precision: 0
        }
      }
    }
  });

  const makeDoughnutOptions = (field, values) => ({
    responsive: true,
    maintainAspectRatio: false,
    onClick(event, elements) {
      if (!elements.length) return;
      const index = elements[0].index;
      applyFilter(field, values[index]);
    },
    plugins: {
      legend: { display: false },
      tooltip: { enabled: false }
    }
  });

  const renderBar = (id, source, field, horizontal) => {
    const canvas = document.getElementById(id);
    if (!canvas || !source || !source.labels || !source.labels.length) return;
    new Chart(canvas, {
      type: "bar",
      data: {
        labels: source.labels,
        datasets: [{
          data: source.totals || [],
          backgroundColor: buildShades(source.labels.length, 0.82),
          borderWidth: 0,
          minBarLength: 8,
          borderRadius: 8
        }]
      },
      options: makeOptions(field, source.values || [], horizontal),
      plugins: [fixedLabels]
    });
  };

  const renderDoughnut = (id, source, field) => {
    const canvas = document.getElementById(id);
    if (!canvas || !source || !source.labels || !source.labels.length) return;
    new Chart(canvas, {
      type: "doughnut",
      data: {
        labels: source.labels,
        datasets: [{
          data: source.totals || [],
          backgroundColor: buildShades(source.labels.length, 0.88),
          borderColor: "#ffffff",
          borderWidth: 4,
          spacing: 3,
          hoverOffset: 10
        }]
      },
      options: makeDoughnutOptions(field, source.values || []),
      plugins: [fixedLabels]
    });
  };

  renderDoughnut("citasPorServicio", data.servicio, "servicio");
  renderBar("citasPorVendedor", data.vendedor, "vendedor", false);
  renderBar("citasPorSeguimiento", data.estatus_seguimiento, "estatus_seguimiento", false);
  renderDoughnut("citasPorPosibilidad", data.posibilidad, "posibilidad");
  renderBar("citasPorMes", data.mes, "mes", false);
})();
