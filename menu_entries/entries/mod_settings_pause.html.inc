<!-- Mod Settings -->
                    <div name="Mod Settings Button"
                         class="list_entry_cntr"
                         data-menu-entries="@MENU_ENTRIES_VERSION@"
                         style="display: none;">
                        <gbx-component name="list_button"
                                       gbx-component-id="list_button"
                                       data-input-behavior-right="lobby_nav"
                                       class="list_entry_list_btn full_absolute_size list_entry"></gbx-component>
                        <mod-settings-hook host="pause" style="display: none;"></mod-settings-hook>
                        <menu-entries-hook mod="mod_settings" style="display: none;"></menu-entries-hook>
                    </div>
