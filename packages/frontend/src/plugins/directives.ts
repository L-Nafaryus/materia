export const clickOutside = {
    beforeMount: function(element: any, binding: any) {
        element.clickOutsideEvent = function(event: any) {
            if (!(element == event.target || element.contains(event.target))) {
                binding.value(event);
            }
        };

        document.body.addEventListener("click", element.clickOutsideEvent);
        document.body.addEventListener("contextmenu", element.clickOutsideEvent);
    },
    unmounted: function(element: any) {
        document.body.removeEventListener("click", element.clickOutsideEvent);
        document.body.removeEventListener("contextmenu", element.clickOutsideEvent);
    }
};

export const tooltip = {
    beforeMount: function (element: any, binding: any) {
        element.tooltip = function (event) {
            let target = event.target;
            if (target.offsetWidth < target.scrollWidth) {
                target.setAttribute('title', binding.value?.text ? binding.value.text : event.target.textContent);
            } else {
                target.hasAttribute('title') && target.removeAttribute('title');
            }
        };

        document.body.addEventListener('mouseover', element.tooltip);
    },
    unmounted: function(element: any) {
        document.body.removeEventListener("mouseover", element.tooltip);
    }
};
