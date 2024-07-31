export const click_outside = {
    beforeMount: function(element: any, binding: any) {
        element.clickOutsideEvent = function(event: any) {
            if (!(element == event.target || element.contains(event.target))) {
                binding.value(event);
            }
        };

        document.body.addEventListener("click", element.clickOutsideEvent);
    },
    unmounted: function(element: any) {
        document.body.removeEventListener("click", element.clickOutsideEvent);
    }
}
