const adCategory = document.getElementById("id_category");
const adSubcategory = document.getElementById("id_subcategory");

if (adCategory && adSubcategory) {
  const groups = Array.from(adSubcategory.querySelectorAll("optgroup"));

  function refreshSubcategories() {
    const categoryName = adCategory.selectedOptions[0]?.textContent.trim();
    const group = groups.find((candidate) => candidate.label === categoryName);
    const previous = adSubcategory.value;
    groups.forEach((candidate) => candidate.remove());

    if (group) {
      adSubcategory.append(group);
    }
    adSubcategory.value = Array.from(adSubcategory.options).some(
      (option) => option.value === previous
    ) ? previous : "";
    adSubcategory.disabled = !group;
  }

  adCategory.addEventListener("change", refreshSubcategories);
  refreshSubcategories();
}
