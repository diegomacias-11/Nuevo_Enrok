(function () {
  var selectedColumns = [];
  var previewRows = [];

  function loadPreviewRows() {
    var node = document.getElementById("report-preview-rows");
    if (!node) return [];
    try {
      return JSON.parse(node.textContent || "[]");
    } catch (error) {
      return [];
    }
  }

  function replaceTokens(value) {
    var today = new Date();
    var formattedDate = today.toLocaleDateString("es-MX", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric"
    });
    return (value || "").replaceAll("{fecha}", formattedDate);
  }

  function formatDateInput(value) {
    if (!value) return "";
    var parts = value.split("-");
    if (parts.length !== 3) return value;
    return parts[2] + "-" + parts[1] + "-" + parts[0];
  }

  function setOutput(name, value, active) {
    var output = document.querySelector('[data-preview-output="' + name + '"]');
    if (!output) return;
    output.hidden = !active;
    output.textContent = active ? replaceTokens(name === "date" ? formatDateInput(value) : value) : "";
  }

  function syncPdfOptionInputs() {
    document.querySelectorAll("[data-preview-field]").forEach(function (field) {
      var name = field.getAttribute("data-preview-field");
      var toggle = document.querySelector('[data-preview-toggle="' + name + '"]');
      if (!toggle) return;
      if (name === "date") {
        field.readOnly = true;
        field.disabled = false;
        return;
      }
      field.disabled = !toggle.checked;
    });
  }

  function syncReportPanels() {
    var archivo = document.getElementById("archivo");
    var selected = archivo ? archivo.value : "pdf";
    document.querySelectorAll("[data-report-panel]").forEach(function (panel) {
      panel.hidden = panel.getAttribute("data-report-panel") !== selected;
    });
    syncColumnsSection();
  }

  function syncColumnsSection() {
    var section = document.querySelector("[data-columns-section]");
    var archivo = document.getElementById("archivo");
    var tableToggle = document.querySelector('[data-preview-toggle="table"]');
    if (!section || !archivo || !tableToggle) return;

    var disabled = archivo.value === "pdf" && !tableToggle.checked;
    section.classList.toggle("is-disabled", disabled);
    section.querySelectorAll("input, select, textarea, button").forEach(function (field) {
      field.disabled = disabled;
    });
  }

  function setPreviewMessage(message) {
    var node = document.querySelector("[data-preview-message]");
    if (!node) return;
    node.hidden = !message;
    node.textContent = message || "";
  }

  function getColumnInputs() {
    return Array.from(document.querySelectorAll('[name="columnas"]'));
  }

  function getTotalColumnMap() {
    var inputs = Array.from(document.querySelectorAll('input[name="columnas_totales"]'));
    var totals = {};
    if (inputs.length) {
      inputs.forEach(function (input) {
        if (input.checked) totals[input.value] = true;
      });
      return totals;
    }

    var list = document.querySelector("[data-column-order-list]");
    var initialValues = list && list.dataset.totalColumns ? list.dataset.totalColumns.split(",") : [];
    initialValues.forEach(function (value) {
      if (value) totals[value] = true;
    });
    return totals;
  }

  function syncSelectedColumns() {
    var checked = getColumnInputs().filter(function (input) {
      return input.checked;
    });
    var checkedMap = {};
    var totalMap = getTotalColumnMap();
    checked.forEach(function (input) {
      checkedMap[input.value] = {
        value: input.value,
        label: input.getAttribute("data-column-label") || input.value,
        isNumeric: input.getAttribute("data-column-numeric") === "1",
        total: !!totalMap[input.value]
      };
    });
    var checkedValues = Object.keys(checkedMap);
    var currentOrder = Array.from(document.querySelectorAll(".report-column-order-item")).map(function (item) {
      return item.dataset.columnValue || item.dataset.columnOrderItem;
    });
    if (!currentOrder.length) {
      var hiddenOrder = document.querySelector("[data-column-order-input]");
      currentOrder = hiddenOrder && hiddenOrder.value ? hiddenOrder.value.split(",") : [];
    }
    var orderedValues = currentOrder.filter(function (value) {
      return checkedValues.indexOf(value) !== -1;
    });

    checkedValues.forEach(function (value) {
      if (orderedValues.indexOf(value) === -1) {
        orderedValues.push(value);
      }
    });

    selectedColumns = orderedValues.map(function (value) {
      return checkedMap[value];
    });
  }

  function copyConfigToFilterForm(filterForm) {
    var constructorForm = document.querySelector(".form-container form");
    if (!constructorForm || !filterForm) return;
    filterForm.querySelectorAll("[data-report-config-hidden]").forEach(function (node) {
      node.remove();
    });
    Array.from(new FormData(constructorForm).entries()).forEach(function (entry) {
      var name = entry[0];
      var value = entry[1];
      if (["csrfmiddlewaretoken", "source", "next"].indexOf(name) !== -1) return;
      var hasNativeFilterField = Array.from(filterForm.elements).some(function (element) {
        return element.name === name && !element.hasAttribute("data-report-config-hidden");
      });
      if (hasNativeFilterField) return;
      var input = document.createElement("input");
      input.type = "hidden";
      input.name = name;
      input.value = value;
      input.setAttribute("data-report-config-hidden", "1");
      filterForm.appendChild(input);
    });
  }

  function syncSelectedColumnsFromOrderDom() {
    var checkedMap = {};
    var totalMap = getTotalColumnMap();
    getColumnInputs().forEach(function (input) {
      if (!input.checked) return;
      checkedMap[input.value] = {
        value: input.value,
        label: input.getAttribute("data-column-label") || input.value,
        isNumeric: input.getAttribute("data-column-numeric") === "1",
        total: !!totalMap[input.value]
      };
    });

    selectedColumns = Array.from(document.querySelectorAll(".report-column-order-item"))
      .map(function (item) {
        return checkedMap[item.dataset.columnValue || item.dataset.columnOrderItem];
      })
      .filter(Boolean);
  }

  function renderColumnOrder() {
    var list = document.querySelector("[data-column-order-list]");
    var hidden = document.querySelector("[data-column-order-input]");
    if (!list) return;

    list.innerHTML = "";
    if (hidden) {
      hidden.value = selectedColumns.map(function (column) {
        return column.value;
      }).join(",");
    }

    if (!selectedColumns.length) {
      var empty = document.createElement("p");
      empty.className = "report-empty-state";
      empty.textContent = "Activa columnas para ordenarlas.";
      list.appendChild(empty);
      return;
    }

    selectedColumns.forEach(function (column) {
      var item = document.createElement("div");
      item.className = "report-column-order-item";
      item.draggable = true;
      item.dataset.columnValue = column.value;

      var handle = document.createElement("span");
      handle.className = "report-column-drag-handle";
      handle.textContent = "::";

      var label = document.createElement("span");
      label.className = "report-column-label";
      label.textContent = column.label;

      item.appendChild(handle);
      item.appendChild(label);
      if (column.isNumeric) {
        var totalLabel = document.createElement("label");
        totalLabel.className = "checkbox-list-toggle report-column-total-toggle";
        totalLabel.title = "Agregar total de esta columna";

        var totalText = document.createElement("span");
        totalText.textContent = "Total";

        var switchNode = document.createElement("span");
        switchNode.className = "toggle-switch";

        var totalInput = document.createElement("input");
        totalInput.type = "checkbox";
        totalInput.name = "columnas_totales";
        totalInput.value = column.value;
        totalInput.checked = !!column.total;

        switchNode.appendChild(totalInput);
        totalLabel.appendChild(totalText);
        totalLabel.appendChild(switchNode);
        item.appendChild(totalLabel);
      }
      list.appendChild(item);
    });
  }

  function moveColumn(fromValue, toValue) {
    if (!fromValue || !toValue || fromValue === toValue) return;
    var fromIndex = selectedColumns.findIndex(function (column) {
      return column.value === fromValue;
    });
    var toIndex = selectedColumns.findIndex(function (column) {
      return column.value === toValue;
    });
    if (fromIndex < 0 || toIndex < 0) return;
    var moved = selectedColumns.splice(fromIndex, 1)[0];
    selectedColumns.splice(toIndex, 0, moved);
    renderColumnOrder();
  }

  function updateTable() {
    var tableBlock = document.querySelector('[data-preview-output="table"]');
    var tableToggle = document.querySelector('[data-preview-toggle="table"]');
    var head = document.querySelector("[data-preview-table-head]");
    var body = document.querySelector(".report-preview-table tbody");
    if (!tableBlock || !tableToggle || !head || !body) return;

    var columns = selectedColumns;

    var showTable = tableToggle.checked && columns.length > 0;
    tableBlock.hidden = !showTable;
    head.innerHTML = "";
    body.innerHTML = "";
    if (tableToggle.checked && !columns.length) {
      setPreviewMessage("Activa al menos una columna para ver la tabla.");
      return;
    }
    if (!showTable) return;

    columns.forEach(function (column) {
      var th = document.createElement("th");
      th.textContent = column.label;
      head.appendChild(th);
    });

    if (!previewRows.length) {
      var emptyTr = document.createElement("tr");
      var emptyTd = document.createElement("td");
      emptyTd.colSpan = columns.length;
      emptyTd.textContent = "Sin datos para vista previa.";
      emptyTr.appendChild(emptyTd);
      body.appendChild(emptyTr);
      return;
    }

    var rows = previewRows;
    rows.forEach(function (previewRow) {
      var tr = document.createElement("tr");
      columns.forEach(function (column) {
        var td = document.createElement("td");
        td.textContent = previewRow[column.value] || "";
        tr.appendChild(td);
      });
      body.appendChild(tr);
    });

    var totalColumns = columns.filter(function (column) {
      return column.total && column.isNumeric;
    });
    if (totalColumns.length) {
      var totals = {};
      totalColumns.forEach(function (column) {
        totals[column.value] = rows.reduce(function (acc, row) {
          var val = row[column.value];
          val = typeof val === "string" ? val.replace(/[^\d.-]/g, "") : val;
          var num = parseFloat(val);
          return acc + (isNaN(num) ? 0 : num);
        }, 0);
      });
      var totalTr = document.createElement("tr");
      totalTr.className = "report-preview-total-row";
      columns.forEach(function (column) {
        var td = document.createElement("td");
        if (totals[column.value] !== undefined) {
          td.textContent = formatMiles(totals[column.value]);
          td.style.fontWeight = "bold";
        } else {
          td.textContent = "";
        }
        totalTr.appendChild(td);
      });
      body.appendChild(totalTr);
    }

    function formatMiles(num) {
      if (typeof num !== "number") return "";
      return num.toLocaleString("es-MX", { maximumFractionDigits: 0 });
    }
  }

  function updatePreview() {
    syncSelectedColumnsFromOrderDom();
    syncPdfOptionInputs();
    setPreviewMessage("");
    ["title", "subtitle", "date", "paragraph", "footer"].forEach(function (name) {
      var toggle = document.querySelector('[data-preview-toggle="' + name + '"]');
      var field = document.querySelector('[data-preview-field="' + name + '"]');
      setOutput(name, field ? field.value : "", toggle ? toggle.checked : false);
    });
    updateTable();
    var hasVisibleBlock = Array.from(document.querySelectorAll("[data-preview-output]")).some(function (node) {
      return !node.hidden;
    });
    if (!hasVisibleBlock) {
      setPreviewMessage("Selecciona opciones y actualiza la vista previa.");
    }
  }

  document.addEventListener("dragstart", function (event) {
    var item = event.target.closest(".report-column-order-item");
    if (!item) return;
    item.classList.add("is-dragging");
    event.dataTransfer.setData("text/plain", item.dataset.columnValue);
  });

  document.addEventListener("dragend", function (event) {
    var item = event.target.closest(".report-column-order-item");
    if (item) item.classList.remove("is-dragging");
  });

  document.addEventListener("dragover", function (event) {
    if (!event.target.closest(".report-column-order-item")) return;
    event.preventDefault();
  });

  document.addEventListener("drop", function (event) {
    var item = event.target.closest(".report-column-order-item");
    if (!item) return;
    event.preventDefault();
    moveColumn(event.dataTransfer.getData("text/plain"), item.dataset.columnValue);
  });

  document.addEventListener("input", syncSelectedColumns);
  document.addEventListener("change", function (event) {
    if (event.target && event.target.id === "archivo") {
      syncReportPanels();
    }
    if (event.target && event.target.name === "columnas") {
      syncSelectedColumns();
      renderColumnOrder();
    }
    if (event.target && event.target.name === "columnas_totales") {
      syncSelectedColumnsFromOrderDom();
    }
    if (event.target && event.target.matches("[data-preview-toggle]")) {
      syncPdfOptionInputs();
      syncColumnsSection();
    }
  });
  document.addEventListener("click", function (event) {
    if (!event.target.closest("[data-preview-refresh]")) return;
    updatePreview();
  });
  document.addEventListener("submit", function (event) {
    var form = event.target;
    if (!form.matches(".filter-form-simple")) return;
    syncSelectedColumnsFromOrderDom();
    renderColumnOrder();
    copyConfigToFilterForm(form);
  });
  document.addEventListener("DOMContentLoaded", function () {
    previewRows = loadPreviewRows();
    syncSelectedColumns();
    renderColumnOrder();
    syncPdfOptionInputs();
    syncReportPanels();
    syncColumnsSection();
  });
})();
