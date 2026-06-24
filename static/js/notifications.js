(function () {
  'use strict';

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      return parts.pop().split(';').shift();
    }
    return '';
  }

  function getCsrfToken() {
    return getCookie('csrftoken');
  }

  function updateBadge(count) {
    const badge = document.getElementById('notificationBellBadge');
    const button = document.getElementById('notificationBellButton');
    if (!badge || !button) {
      return;
    }

    if (!count) {
      badge.classList.add('d-none');
      badge.textContent = '';
      return;
    }

    badge.classList.remove('d-none');
    badge.textContent = count > 9 ? '9+' : String(count);
  }

  function updateDropdownUnreadCount(count) {
    const subtitle = document.querySelector('.notification-dropdown__subtitle');
    const countEl = document.getElementById('notificationDropdownUnreadCount');
    if (!subtitle || !countEl) {
      return;
    }

    if (!count) {
      subtitle.classList.add('notification-dropdown__subtitle--muted');
      subtitle.innerHTML = 'همه اعلان‌ها خوانده شده‌اند';
      const markAll = document.querySelector('[data-notification-mark-all]');
      if (markAll) {
        markAll.remove();
      }
      return;
    }

    countEl.textContent = String(count);
  }

  async function postJson(url) {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCsrfToken(),
        'X-Requested-With': 'XMLHttpRequest',
      },
      credentials: 'same-origin',
    });
    if (!response.ok) {
      throw new Error('Request failed');
    }
    return response.json();
  }

  function positionPanel(panel, button) {
    const rect = button.getBoundingClientRect();
    const panelWidth = Math.min(320, window.innerWidth - 16);
    panel.style.width = `${panelWidth}px`;

    let left = rect.left;
    if (left + panelWidth > window.innerWidth - 8) {
      left = window.innerWidth - panelWidth - 8;
    }
    if (left < 8) {
      left = 8;
    }

    panel.style.left = `${left}px`;
    panel.style.top = `${rect.bottom + 8}px`;
  }

  function initNotificationBell() {
    const root = document.getElementById('notificationBellRoot');
    const button = document.getElementById('notificationBellButton');
    const panel = document.getElementById('notificationBellPanel');
    const panelContent = document.getElementById('notificationBellPanelContent');
    const loading = document.getElementById('notificationBellLoading');

    if (!root || !button || !panel || !panelContent) {
      return;
    }

    const dropdownUrl = button.dataset.dropdownUrl;
    const markAllUrl = button.dataset.markAllUrl;
    let isOpen = false;
    let hasLoaded = false;

    function closePanel() {
      isOpen = false;
      panel.hidden = true;
      button.setAttribute('aria-expanded', 'false');
    }

    function openPanel() {
      isOpen = true;
      panel.hidden = false;
      button.setAttribute('aria-expanded', 'true');
      positionPanel(panel, button);
    }

    async function loadDropdown(forceReload) {
      if (hasLoaded && !forceReload) {
        return;
      }

      if (loading) {
        loading.hidden = false;
      }

      try {
        const response = await fetch(dropdownUrl, {
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
          credentials: 'same-origin',
        });
        if (!response.ok) {
          throw new Error('Failed to load notifications');
        }
        const html = await response.text();
        panelContent.innerHTML = html;
        hasLoaded = true;
        bindDropdownActions();
      } catch (error) {
        panelContent.innerHTML =
          '<div class="notification-dropdown__empty"><p>بارگذاری اعلان‌ها ناموفق بود.</p></div>';
      } finally {
        if (loading) {
          loading.hidden = true;
        }
      }
    }

    async function markNotificationRead(notificationId) {
      const data = await postJson(`/notifications/${notificationId}/read/`);
      updateBadge(data.unread_count);
      updateDropdownUnreadCount(data.unread_count);
      return data;
    }

    async function markAllRead() {
      const data = await postJson(markAllUrl);
      updateBadge(0);
      document.querySelectorAll('.notification-dropdown__item.is-unread').forEach((item) => {
        item.classList.remove('is-unread');
      });
      updateDropdownUnreadCount(0);
      return data;
    }

    function bindDropdownActions() {
      const markAllButton = panelContent.querySelector('[data-notification-mark-all]');
      if (markAllButton) {
        markAllButton.addEventListener('click', async (event) => {
          event.preventDefault();
          event.stopPropagation();
          try {
            await markAllRead();
          } catch (error) {
            /* no-op */
          }
        });
      }

      panelContent.querySelectorAll('[data-notification-id]').forEach((item) => {
        item.addEventListener('click', async (event) => {
          const notificationId = item.dataset.notificationId;
          const targetUrl = item.dataset.notificationUrl;
          const noUrl = item.dataset.notificationNoUrl === 'true';

          if (noUrl) {
            event.preventDefault();
          }

          try {
            await markNotificationRead(notificationId);
            item.classList.remove('is-unread');
          } catch (error) {
            /* continue navigation if URL exists */
          }

          if (noUrl) {
            closePanel();
          }
        });
      });
    }

    button.addEventListener('click', async (event) => {
      event.preventDefault();
      event.stopPropagation();

      if (isOpen) {
        closePanel();
        return;
      }

      openPanel();
      await loadDropdown(true);
    });

    document.addEventListener('click', (event) => {
      if (!isOpen) {
        return;
      }
      if (!root.contains(event.target)) {
        closePanel();
      }
    });

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && isOpen) {
        closePanel();
      }
    });

    window.addEventListener('resize', () => {
      if (isOpen) {
        positionPanel(panel, button);
      }
    });
  }

  function initNotificationsPage() {
    const markAllButton = document.getElementById('notificationsPageMarkAll');
    if (!markAllButton) {
      return;
    }

    markAllButton.addEventListener('click', async () => {
      try {
        await postJson(markAllButton.dataset.markAllUrl);
        document.querySelectorAll('.notifications-page__item.is-unread').forEach((item) => {
          item.classList.remove('is-unread');
        });
        const subtitle = document.querySelector('.notifications-page__subtitle');
        if (subtitle) {
          subtitle.remove();
        }
        markAllButton.remove();
        updateBadge(0);
      } catch (error) {
        /* no-op */
      }
    });

    document.querySelectorAll('[data-notification-link]').forEach((link) => {
      link.addEventListener('click', async () => {
        const notificationId = link.dataset.notificationLink;
        try {
          await postJson(`/notifications/${notificationId}/read/`);
          const item = link.closest('.notifications-page__item');
          if (item) {
            item.classList.remove('is-unread');
          }
        } catch (error) {
          /* no-op */
        }
      });
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    initNotificationBell();
    initNotificationsPage();
  });
})();
