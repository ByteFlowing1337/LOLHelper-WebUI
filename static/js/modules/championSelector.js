// championSelector.js - Champion selection component with search and avatar display

// Load champion data
let championData = {};

// Initialize champion data from JSON
async function loadChampionData() {
  try {
    const response = await fetch("/static/data/champion_map.json");
    championData = await response.json();
    console.log("Champion data loaded successfully");
  } catch (error) {
    console.error("Failed to load champion data:", error);
    // Fallback data (using common champions as examples)
    championData = {
      1: "Annie",
      157: "Yasuo",
      555: "Pyke",
      238: "Zed",
      64: "LeeSin",
    };
  }
}

// Get champion avatar URL (using community dragon CDN)
function getChampionAvatarUrl(championName) {
  // Use community dragon CDN for champion icons
  return `https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-icons/${getChampionId(
    championName
  )}.png`;
}

// Get champion ID by name
function getChampionId(championName) {
  for (const [id, name] of Object.entries(championData)) {
    if (name.toLowerCase() === championName.toLowerCase()) {
      return id;
    }
  }
  return null;
}

// Get champion name by ID
function getChampionName(championId) {
  return championData[championId] || "";
}

// Create champion selector component
function createChampionSelector(elementId, placeholder = "") {
  const container = document.getElementById(elementId);
  if (!container) {
    console.error(`Element with ID '${elementId}' not found`);
    return null;
  }

  // Create the main selector structure
  container.innerHTML = `
    <div class="champion-selector">
      <div class="champion-selector-display" tabindex="0">
        <div class="champion-selected">
          <div class="champion-avatar-placeholder">
            <i class="bi bi-person-plus"></i>
          </div>
          <span class="champion-name">${placeholder}</span>
        </div>
        <i class="bi bi-chevron-down dropdown-arrow"></i>
      </div>
      <div class="champion-dropdown">
        <div class="champion-search">
          <input type="text" class="champion-search-input" placeholder="搜索英雄名称...">
        </div>
        <div class="champion-list"></div>
      </div>
    </div>
  `;

  const selector = container.querySelector(".champion-selector");
  const display = selector.querySelector(".champion-selector-display");
  const dropdown = selector.querySelector(".champion-dropdown");
  const searchInput = selector.querySelector(".champion-search-input");
  const championList = selector.querySelector(".champion-list");
  const selectedAvatar = selector.querySelector(".champion-avatar-placeholder");
  const selectedName = selector.querySelector(".champion-name");
  const dropdownArrow = selector.querySelector(".dropdown-arrow");

  let isOpen = false;
  let selectedChampionId = null;
  let filteredChampions = [];

  // Initialize champion list
  function initializeChampionList() {
    filteredChampions = Object.entries(championData)
      .map(([id, name]) => ({
        id: parseInt(id),
        name: name,
        displayName: formatChampionName(name),
      }))
      .sort((a, b) => a.displayName.localeCompare(b.displayName));

    renderChampionList();
  }

  // Format champion name for display
  function formatChampionName(name) {
    // Handle special cases
    const nameMap = {
      TwistedFate: "Twisted Fate",
      XinZhao: "Xin Zhao",
      MasterYi: "Master Yi",
      MissFortune: "Miss Fortune",
      DrMundo: "Dr. Mundo",
      JarvanIV: "Jarvan IV",
      MonkeyKing: "Wukong",
      LeeSin: "Lee Sin",
      KogMaw: "Kog'Maw",
      AurelionSol: "Aurelion Sol",
      TahmKench: "Tahm Kench",
      RekSai: "Rek'Sai",
      KSante: "K'Sante",
    };

    return nameMap[name] || name.replace(/([A-Z])/g, " $1").trim();
  }

  // Render champion list
  function renderChampionList() {
    championList.innerHTML = "";

    filteredChampions.forEach((champion) => {
      const item = document.createElement("div");
      item.className = "champion-item";
      item.dataset.championId = champion.id;

      item.innerHTML = `
        <div class="champion-avatar">
          <img src="${getChampionAvatarUrl(champion.name)}" 
               alt="${champion.displayName}"
               onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
          <div class="champion-avatar-fallback" style="display: none;">
            <i class="bi bi-person"></i>
          </div>
        </div>
        <span class="champion-item-name">${champion.displayName}</span>
        <small class="champion-item-id">ID: ${champion.id}</small>
      `;

      item.addEventListener("click", () => selectChampion(champion));
      championList.appendChild(item);
    });
  }

  // Filter champions by search term
  function filterChampions(searchTerm) {
    if (!searchTerm) {
      filteredChampions = Object.entries(championData)
        .map(([id, name]) => ({
          id: parseInt(id),
          name: name,
          displayName: formatChampionName(name),
        }))
        .sort((a, b) => a.displayName.localeCompare(b.displayName));
    } else {
      const term = searchTerm.toLowerCase();
      filteredChampions = Object.entries(championData)
        .map(([id, name]) => ({
          id: parseInt(id),
          name: name,
          displayName: formatChampionName(name),
        }))
        .filter(
          (champion) =>
            champion.displayName.toLowerCase().includes(term) ||
            champion.name.toLowerCase().includes(term) ||
            champion.id.toString().includes(term)
        )
        .sort((a, b) => a.displayName.localeCompare(b.displayName));
    }
    renderChampionList();
  }

  // Select a champion
  function selectChampion(champion) {
    selectedChampionId = champion.id;

    // Update display
    selectedAvatar.innerHTML = `
      <img src="${getChampionAvatarUrl(champion.name)}" 
           alt="${champion.displayName}"
           onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
      <div class="champion-avatar-fallback" style="display: none;">
        <i class="bi bi-person"></i>
      </div>
    `;
    selectedName.textContent = champion.displayName;

    closeDropdown();

    // Trigger change event
    const changeEvent = new CustomEvent("championChanged", {
      detail: {
        championId: champion.id,
        championName: champion.name,
        displayName: champion.displayName,
      },
    });
    container.dispatchEvent(changeEvent);
  }

  // Open dropdown
  function openDropdown() {
    if (isOpen) return;

    isOpen = true;
    dropdown.style.display = "block";
    dropdownArrow.classList.add("rotated");
    searchInput.focus();

    // Position dropdown
    const rect = display.getBoundingClientRect();
    dropdown.style.top = `${rect.height}px`;
    dropdown.style.width = `${rect.width}px`;
  }

  // Close dropdown
  function closeDropdown() {
    if (!isOpen) return;

    isOpen = false;
    dropdown.style.display = "none";
    dropdownArrow.classList.remove("rotated");
    searchInput.value = "";
    filterChampions("");
  }

  // Event listeners
  display.addEventListener("click", () => {
    if (isOpen) {
      closeDropdown();
    } else {
      openDropdown();
    }
  });

  display.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      if (isOpen) {
        closeDropdown();
      } else {
        openDropdown();
      }
    }
  });

  searchInput.addEventListener("input", (e) => {
    filterChampions(e.target.value);
  });

  searchInput.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeDropdown();
    }
  });

  // Close dropdown when clicking outside
  document.addEventListener("click", (e) => {
    if (!selector.contains(e.target)) {
      closeDropdown();
    }
  });

  // Initialize
  initializeChampionList();

  // Public API
  return {
    getSelectedChampionId: () => selectedChampionId,
    setSelectedChampion: (championId) => {
      const champion = filteredChampions.find(
        (c) => c.id === parseInt(championId)
      );
      if (champion) {
        selectChampion(champion);
      }
    },
    clearSelection: () => {
      selectedChampionId = null;
      selectedAvatar.innerHTML = '<i class="bi bi-person-plus"></i>';
      selectedName.textContent = placeholder;
    },
  };
}

// Export functions
export {
  loadChampionData,
  createChampionSelector,
  getChampionName,
  getChampionId,
  getChampionAvatarUrl,
};
